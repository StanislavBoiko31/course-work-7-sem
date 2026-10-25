import csv
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

from switching_node import SwitchingNodeModel

RESULTS = Path(__file__).resolve().parent.parent / "results"
RESULTS.mkdir(exist_ok=True)

T_WARMUP = 200.0
T_MOD = 40000.0
N_RUNS = 35


def replicate(params, n_runs=N_RUNS, t_mod=T_MOD, t_warmup=T_WARMUP,
              seed0=1):
    return [SwitchingNodeModel(params, seed=seed0 + i)
            .simulate(t_mod, t_warmup) for i in range(n_runs)]


def mean_sd(values):
    n = len(values)
    mean = sum(values) / n
    if n < 2:
        return mean, 0.0
    return mean, math.sqrt(sum((v - mean) ** 2 for v in values) / (n - 1))


def runs_needed(sd, eps, beta=0.95):
    return math.ceil(sd ** 2 / (eps ** 2 * (1.0 - beta)))


def save_csv(name, rows):
    path = RESULTS / name
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()),
                           delimiter=";")
        w.writeheader()
        w.writerows(rows)
    return path


def comma(x, _pos=None):
    return f"{x:g}".replace(".", ",").replace("-", "−")


def setup_plots():
    plt.rcParams.update({
        "font.family": "Times New Roman",
        "font.size": 12,
        "axes.titlesize": 12,
        "legend.fontsize": 10,
        "figure.dpi": 100,
        "savefig.dpi": 300,
        "axes.grid": True,
        "grid.alpha": 0.3,
    })


def finish(fig, name):
    for ax in fig.axes:
        if ax.get_label() == "<colorbar>":
            continue
        ax.xaxis.set_major_formatter(FuncFormatter(comma))
        ax.yaxis.set_major_formatter(FuncFormatter(comma))
    fig.tight_layout()
    for ext in ("png", "svg"):
        fig.savefig(RESULTS / f"{name}.{ext}", bbox_inches="tight")
    plt.close(fig)
