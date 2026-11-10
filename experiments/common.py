import csv
import math
import random
import sys
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
N_RUNS = 36

_seed_rng = random.Random()
_used_seeds = set()


def start_experiment(name):
    if "--seed" in sys.argv:
        seed = int(sys.argv[sys.argv.index("--seed") + 1])
    else:
        seed = random.SystemRandom().randrange(1, 2 ** 31)
    _seed_rng.seed(seed)
    _used_seeds.clear()
    path = RESULTS / "seeds.csv"
    rows = []
    if path.exists():
        with open(path, encoding="utf-8-sig") as f:
            rows = [r for r in csv.DictReader(f, delimiter=";")
                    if r["дослід"] != name]
    save_csv("seeds.csv", rows + [{"дослід": name, "зерно": seed}])
    print(f"{name}: початкове зерно {seed}", flush=True)
    return seed


def new_seeds(n):
    seeds = []
    while len(seeds) < n:
        s = _seed_rng.randrange(1, 2 ** 31)
        if s not in _used_seeds:
            _used_seeds.add(s)
            seeds.append(s)
    return seeds


def replicate(params, n_runs=N_RUNS, t_mod=T_MOD, t_warmup=T_WARMUP):
    return [SwitchingNodeModel(params, seed=s).simulate(t_mod, t_warmup)
            for s in new_seeds(n_runs)]


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
