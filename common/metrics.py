""" Accuracy, macro-F1, log-loss, one-vs-rest AUC, the confusion matrix, bootstrap interval for the macro-F1."""
from __future__ import annotations
import numpy as np

def softmax(logits: np.ndarray) -> np.ndarray:
    z = logits - logits.max(1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(1, keepdims=True)

def ece(y: np.ndarray, P: np.ndarray, bins: int = 15) -> float:
    """Expected calibration error over equal-width confidence bins."""
    pred, conf = P.argmax(1), P.max(1)
    edges = np.linspace(0, 1, bins + 1)
    e = 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (conf > lo) & (conf <= hi)
        if m.any():
            e += m.mean() * abs((pred[m] == y[m]).mean() - conf[m].mean())
    return float(e)

def evaluate(y: np.ndarray, P: np.ndarray) -> dict:
    from sklearn.metrics import f1_score, log_loss, roc_auc_score
    P = np.asarray(P, np.float64)
    P = P / np.maximum(P.sum(1, keepdims=True), 1e-12)
    pred = P.argmax(1)
    K = P.shape[1]
    try:
        auc = float(roc_auc_score(y, P, multi_class="ovr", average="macro", labels=list(range(K))))
    except ValueError:
        auc = float("nan")
    return {"accuracy": float((pred == y).mean()), "macro_f1": float(f1_score(y, pred, average="macro", zero_division=0)),
            "log_loss": float(log_loss(y, np.clip(P, 1e-12, 1), labels=list(range(K)))), "auc_ovr_macro": auc, "ece_15": ece(y, P)}

def confusion(y: np.ndarray, pred: np.ndarray, K: int) -> np.ndarray:
    M = np.zeros((K, K), np.int64)
    np.add.at(M, (y, pred), 1)
    return M

def macro_f1(y: np.ndarray, pred: np.ndarray, K: int) -> float:
    from sklearn.metrics import f1_score
    return float(f1_score(y, pred, average="macro", labels=list(range(K)), zero_division=0))

def bootstrap_macro_f1(y: np.ndarray, pred: np.ndarray, K: int, n_boot: int = 1000, seed: int = 0) -> dict:
    """Percentile interval of the macro-F1 over resampled rows of one held-out set."""
    rng = np.random.RandomState(seed)
    n = len(y)
    scores = [macro_f1(y[idx], pred[idx], K) for idx in (rng.randint(0, n, n) for _ in range(n_boot))]
    return {"macro_f1": macro_f1(y, pred, K), "ci_low": float(np.percentile(scores, 2.5)), "ci_high": float(np.percentile(scores, 97.5)), "n_boot": n_boot}

def fit_temperature(logits: np.ndarray, y: np.ndarray) -> float:
    """The scalar T that minimises the cross-entropy of softmax(logits / T)."""
    from scipy.optimize import minimize_scalar
    z = logits.astype(np.float64)

    def nll(T):
        P = softmax(z / T)
        return -np.mean(np.log(np.clip(P[np.arange(len(y)), y], 1e-12, 1)))
    return float(minimize_scalar(nll, bounds=(0.05, 20.0), method="bounded", options={"xatol": 1e-4}).x)
