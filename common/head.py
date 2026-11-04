"""The head. 
Training minimises the sum of the readings' cross-entropies with AdamW, a one-epoch warm-up and a cosine decay, keeps an
exponential moving average of the weights, and stops early on the validation cross-entropy of the averaged weights. 
Inference and the JSON export sits here too for consistency when every script is read."""
from __future__ import annotations
import copy
import math
import time
import numpy as np
import torch
from torch import nn
from .metrics import evaluate, softmax

OPTIMISER = {"batch": 256, "warmup_epochs": 1, "cosine_floor": 0.1, "ema": 0.999, "max_epochs": 100, "patience": 10}

def make_activation(name: str) -> nn.Module:
    return {"relu": nn.ReLU, "gelu": nn.GELU, "silu": nn.SiLU, "tanh": nn.Tanh, "elu": nn.ELU, "sigmoid": nn.Sigmoid, "leaky_relu": lambda: nn.LeakyReLU(0.01)}[name]()

class MultiHead(nn.Module):
    def __init__(self, p: int, widths: list[int], acts: list[str], dropout: float, n_classes: list[int], input_dropout: float = 0.0):
        super().__init__()
        layers: list[nn.Module] = []
        if input_dropout > 0:
            layers.append(nn.Dropout(input_dropout))
        d = p
        for w, a in zip(widths, acts):
            layers += [nn.Linear(d, w), make_activation(a)]
            if dropout > 0:
                layers.append(nn.Dropout(dropout))
            d = w
        self.trunk = nn.Sequential(*layers)
        self.outs = nn.ModuleList([nn.Linear(d, k) for k in n_classes])
        self.p, self.widths, self.acts, self.n_classes = p, list(widths), list(acts), list(n_classes)

    def forward(self, x):
        h = self.trunk(x)
        return [o(h) for o in self.outs]

    def n_params(self) -> int:
        return sum(q.numel() for q in self.parameters())

    def trunk_linears(self) -> list[nn.Linear]:
        return [m for m in self.trunk if isinstance(m, nn.Linear)]

    def describe(self, names: list[str]) -> str:
        hidden = [f"{w} ({a})" for w, a in zip(self.widths, self.acts)]
        outs = " | ".join(f"{k} (softmax, {n})" for k, n in zip(self.n_classes, names))
        return " -> ".join([str(self.p)] + hidden + [f"[{outs}]"])

# features
def standardise(X_tr: np.ndarray, *others):
    """Matrix standardisation."""
    mean = X_tr.mean(0)
    sd = X_tr.std(0)
    sd = np.where(sd < 1e-8, 1.0, sd)
    return mean, sd, [((X - mean) / sd).astype(np.float32) for X in (X_tr,) + others]

def standardise_with(mj: dict, X: np.ndarray) -> np.ndarray:
    return ((X - np.array(mj["mean"], np.float32)) / np.array(mj["sd"], np.float32)).astype(np.float32)

def smoothed_targets(y: np.ndarray, K: int, eps: float) -> np.ndarray:
    T = np.full((len(y), K), eps / K, np.float32)
    T[np.arange(len(y)), y] += 1.0 - eps
    return T

# inference
def predict_logits(model: MultiHead, X: np.ndarray, batch: int = 4096) -> list[np.ndarray]:
    model.eval()
    outs: list[list[np.ndarray]] = [[] for _ in model.outs]
    with torch.no_grad():
        for i in range(0, len(X), batch):
            for t, l in enumerate(model(torch.from_numpy(np.ascontiguousarray(X[i:i + batch])))):
                outs[t].append(l.numpy())
    return [np.vstack(o) if o else np.zeros((0, k), np.float32) for o, k in zip(outs, model.n_classes)]

def predict_proba(model: MultiHead, X: np.ndarray, temperatures=None) -> list[np.ndarray]:
    temps = temperatures or [1.0] * len(model.outs)
    return [softmax(l / float(T)) for l, T in zip(predict_logits(model, X), temps)]

# training
def make_schedule(opt, steps_per_epoch: int, horizon_epochs: int, warmup_epochs: float, floor: float):
    warm = max(1, int(round(warmup_epochs * steps_per_epoch)))
    total = max(warm + 1, horizon_epochs * steps_per_epoch)

    def factor(step):
        if step < warm:
            return (step + 1) / warm
        t = min(1.0, (step - warm) / max(1, total - warm))
        return floor + (1.0 - floor) * 0.5 * (1.0 + math.cos(math.pi * t))
    return torch.optim.lr_scheduler.LambdaLR(opt, factor)

class EMA:
    """Making sure the first epochs are not dragged towards the random start."""
    def __init__(self, model: nn.Module, decay: float):
        self.decay = decay
        self.shadow = {k: v.detach().clone() for k, v in model.state_dict().items()}
        self.n = 0

    def update(self, model: nn.Module):
        self.n += 1
        d = min(self.decay, (1 + self.n) / (10 + self.n))
        with torch.no_grad():
            for k, v in model.state_dict().items():
                self.shadow[k].mul_(d).add_(v.detach(), alpha=1 - d)

def soft_cross_entropy(logits, targets):
    return -(targets * torch.log_softmax(logits, dim=1)).sum(1).mean()

def fit(X_tr, Y_tr: list[np.ndarray], X_va, Y_va, head: dict, n_classes: list[int], seed: int, max_epochs: int, patience: int,
        opt_cfg: dict | None = None, horizon_epochs: int | None = None, weights: list[float] | None = None, verbose: bool = False) -> dict:
    """Y_tr and Y_va hold one integer label array per reading. The loss is the weighted sum of the readings' cross-entropies on smoothed one-hot targets.
     Early stopping watches the same sum on the validation rows with the averaged weights, and the weights of the best epoch are kept."""
    o = dict(OPTIMISER)
    o.update(opt_cfg or {})
    torch.manual_seed(seed)
    np.random.seed(seed)
    n_tasks = len(n_classes)
    w = list(weights) if weights else [1.0] * n_tasks
    model = MultiHead(X_tr.shape[1], head["widths"], head["acts"], head["dropout"], n_classes, head.get("input_dropout", 0.0))
    opt = torch.optim.AdamW(model.parameters(), lr=head["lr"], weight_decay=head["weight_decay"])
    batch = int(head.get("batch", o["batch"]))
    n = len(X_tr)
    steps_per_epoch = max(1, math.ceil(n / batch))
    sched = make_schedule(opt, steps_per_epoch, horizon_epochs or max_epochs, o["warmup_epochs"], o["cosine_floor"])
    ema = EMA(model, float(o["ema"])) if float(o.get("ema", 0)) > 0 else None
    Xt = torch.from_numpy(np.ascontiguousarray(X_tr))
    Tt = [torch.from_numpy(smoothed_targets(y, k, float(head.get("smoothing", 0.0)))) for y, k in zip(Y_tr, n_classes)]
    curves = {"train_loss": [], "val_loss": [], "val_macro_f1": [[] for _ in range(n_tasks)], "step_loss": []}
    best, best_state, best_epoch, bad = np.inf, None, 0, 0
    g = torch.Generator().manual_seed(seed)
    t0 = time.time()
    eval_model = model
    for epoch in range(1, max_epochs + 1):
        model.train()
        perm = torch.randperm(n, generator=g)
        total = 0.0
        for i in range(0, n, batch):
            idx = perm[i:i + batch]
            opt.zero_grad()
            loss = sum(w[t] * soft_cross_entropy(l, Tt[t][idx]) for t, l in enumerate(model(Xt[idx])))
            loss.backward()
            opt.step()
            sched.step()
            if ema is not None:
                ema.update(model)
            l = float(loss.detach())
            curves["step_loss"].append(l)
            total += l * len(idx)
        curves["train_loss"].append(total / n)
        if ema is not None:
            eval_model = copy.deepcopy(model)
            eval_model.load_state_dict(ema.shadow)
        if X_va is None:
            continue
        crit = 0.0
        for t, P in enumerate(predict_proba(eval_model, X_va)):
            ev = evaluate(Y_va[t], P)
            crit += w[t] * ev["log_loss"]
            curves["val_macro_f1"][t].append(ev["macro_f1"])
        curves["val_loss"].append(crit)
        if verbose:
            print(f"    epoch {epoch} train {curves['train_loss'][-1]:.4f} val {crit:.4f} f1 " + " ".join(f"{v[-1]:.4f}" for v in curves["val_macro_f1"]), flush=True)
        if crit < best - 1e-5:
            best, best_epoch, bad = crit, epoch, 0
            best_state = copy.deepcopy(eval_model.state_dict())
        else:
            bad += 1
            if bad >= patience:
                break
    if best_state is not None:
        model.load_state_dict(best_state)
    else:
        if ema is not None:
            model.load_state_dict(ema.shadow)
        best_epoch = max_epochs
    model.eval()
    return {"model": model, "best_epoch": best_epoch, "curves": curves, "seconds": time.time() - t0}


# JSON form for predict.py and adapt.py
def to_json(model: MultiHead, readings: list[dict], mean: np.ndarray, sd: np.ndarray, temperatures: list[float], head: dict, extra: dict) -> dict:
    f6 = lambda a: [[float(f"{v:.6g}") for v in row] for row in a]
    trunk = [{"W": f6(m.weight.detach().numpy()), "b": [float(f"{v:.6g}") for v in m.bias.detach().numpy()], "act": a}
             for m, a in zip(model.trunk_linears(), model.acts)]
    tasks = [{"name": r["name"], "classes": r["labels"], "temperature": float(f"{T:.6g}"),
              "out": {"W": f6(o.weight.detach().numpy()), "b": [float(f"{v:.6g}") for v in o.bias.detach().numpy()]}}
             for r, o, T in zip(readings, model.outs, temperatures)]
    mj = {"readings": [r["name"] for r in readings], "p": model.p, "arch": model.describe([r["name"] for r in readings]),
          "config": head, "n_params": model.n_params(), "mean": [float(f"{v:.6g}") for v in mean], "sd": [float(f"{v:.6g}") for v in sd],
          "trunk": trunk, "tasks": tasks}
    mj.update(extra)
    return mj

def from_json(mj: dict) -> MultiHead:
    """The head is stored by to_json ready for inference or for an adaptation."""
    cfg = mj["config"]
    model = MultiHead(mj["p"], cfg["widths"], cfg["acts"], 0.0, [len(t["classes"]) for t in mj["tasks"]], 0.0)
    for m, l in zip(model.trunk_linears(), mj["trunk"]):
        m.weight.data = torch.tensor(l["W"], dtype=torch.float32)
        m.bias.data = torch.tensor(l["b"], dtype=torch.float32)
    for o, t in zip(model.outs, mj["tasks"]):
        o.weight.data = torch.tensor(t["out"]["W"], dtype=torch.float32)
        o.bias.data = torch.tensor(t["out"]["b"], dtype=torch.float32)
    model.eval()
    return model
