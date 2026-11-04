"""The log every test layer writes: one line per check, dated, with its duration, in logs/<stage>_<date>.log,
and the same records as logs/<stage>_<date>.json for anything that reads them back.
    PASS  IT-03  FinGPT Network: confirmation macro-F1 0.7978 in [0.786, 0.809]  (0.4 s)
"""
from __future__ import annotations
import json
import os
import sys
import time
from pathlib import Path

LEVELS = ("INFO", "PASS", "FAIL", "SKIP", "WARN")

class RunLog:
    def __init__(self, stage: str, folder: Path | str, reference: str = "", echo: bool = True):
        self.stage = stage
        self.echo = echo
        self.date = time.strftime("%Y-%m-%d")
        self.folder = Path(folder)
        self.folder.mkdir(parents=True, exist_ok=True)
        stamp = time.strftime("%Y%m%d")
        self.path = self.folder / f"{stage}_{stamp}.log"
        self.json_path = self.folder / f"{stage}_{stamp}.json"
        self.records: list[dict] = []
        self.lines: list[str] = []
        self.t0 = time.time()
        self._fh = open(self.path, "a", encoding="utf-8")
        self.header(reference)

    def header(self, reference: str):
        torch_v = ""
        try:
            import torch
            torch_v = torch.__version__
        except Exception:
            pass
        lines = [f"{self.stage} log, {self.date}",
                 f"job {os.environ.get('SLURM_JOB_ID', 'local')}, python {sys.version.split()[0]}" + (f", torch {torch_v}" if torch_v else "")]
        if reference:
            lines.append(f"reference: {reference}")
        for ln in lines:
            self._write(ln)
        self._write("-" * 100)

    def _write(self, line: str):
        self.lines.append(line)
        self._fh.write(line + "\n")
        self._fh.flush()
        if self.echo:
            print(line, flush=True)

    def text(self) -> str:
        return "\n".join(self.lines) + "\n"

    def line(self, level: str, ident: str, message: str, seconds: float | None = None, **extra):
        level = level.upper()
        tail = f"  ({seconds:.2f} s)" if seconds is not None else ""
        self._write(f"{self.date}  {level:4s}  {ident:<9s} {message}{tail}")
        rec = {"date": self.date, "level": level, "id": ident, "message": message}
        if seconds is not None:
            rec["seconds"] = round(seconds, 3)
        rec.update(extra)
        self.records.append(rec)

    def info(self, message: str, ident: str = "-"):
        self.line("INFO", ident, message)

    def check(self, ident: str, ok: bool, message: str, seconds: float | None = None, **extra):
        self.line("PASS" if ok else "FAIL", ident, message, seconds, **extra)
        return ok

    def skip(self, ident: str, message: str):
        self.line("SKIP", ident, message)

    def counts(self) -> dict:
        c = {k: 0 for k in LEVELS}
        for r in self.records:
            c[r["level"]] += 1
        return c

    def close(self, exit_code: int | None = None) -> int:
        c = self.counts()
        total = time.time() - self.t0
        code = exit_code if exit_code is not None else (1 if c["FAIL"] else 0)
        self._write("-" * 100)
        self._write(f"{self.date}  {'PASS' if code == 0 else 'FAIL'}: {c['PASS']} passed, {c['FAIL']} failed, {c['SKIP']} skipped in {total:.1f} s; exit {code}")
        self._fh.close()
        self.json_path.write_text(json.dumps({"stage": self.stage, "date": self.date, "job": os.environ.get("SLURM_JOB_ID"),
                                              "seconds": round(total, 1), "counts": c, "exit": code, "records": self.records}, indent=1), encoding="utf-8")
        return code

def log_folder() -> Path:
    """The repository's logs/ folder, where the job scripts write their output too, so every record of a run is in one place."""
    return Path(__file__).resolve().parents[1] / "logs"
