import csv
import sys

import matplotlib.pyplot as plt
import numpy as np

from switching_node import ModelParams

from .common import (N_RUNS, RESULTS, finish, mean_sd, replicate, save_csv,
                     setup_plots)

T1_RANGE = (3.0, 7.0)
T2_RANGE = (3.0, 8.0)


def evaluate(t1, t2):
    res = replicate(ModelParams().with_lines(t1, t2), N_RUNS)
    e_mean, e_sd = mean_sd([r.profit_rate for r in res])

    def avg(f):
        return sum(f(r) for r in res) / len(res)

    return {
        "t1": round(t1, 2), "t2": round(t2, 2),
        "E": e_mean, "E_sd": e_sd,
        "lam1": avg(lambda r: r.throughput[0]),
        "lam2": avg(lambda r: r.throughput[1]),
        "P1": avg(lambda r: r.p_fail[0]),
        "P2": avg(lambda r: r.p_fail[1]),
        "rhoL1": avg(lambda r: r.util_line[0]),
        "rhoL2": avg(lambda r: r.util_line[1]),
        "rhoP": avg(lambda r: r.util_proc),
        "W1": avg(lambda r: r.sojourn_mean[0]),
        "W2": avg(lambda r: r.sojourn_mean[1]),
    }


def grid_search(t1_values, t2_values):
    rows = [evaluate(t1, t2) for t1 in t1_values for t2 in t2_values]
    best = max(r["E"] for r in rows)
    print(f"обчислено {len(rows)} точок, найкраще E = {best:.4f}",
          flush=True)
    return rows


def fmt(v, digits=2):
    return f"{v:.{digits}f}".replace(".", ",")


def plot_surface(rows, best, base, name):
    t1s = sorted({r["t1"] for r in rows})
    t2s = sorted({r["t2"] for r in rows})
    E = {(r["t1"], r["t2"]): r["E"] for r in rows}
    Z = np.array([[E[(a, b)] for a in t1s] for b in t2s])
    fig, ax = plt.subplots(figsize=(6.5, 4.8))
    cs = ax.contourf(t1s, t2s, Z, levels=14, cmap="viridis")
    lines = ax.contour(t1s, t2s, Z, levels=cs.levels[::2], colors="k",
                       linewidths=0.5)
    ax.clabel(lines, fmt=fmt, fontsize=9)
    cb = fig.colorbar(cs, ax=ax)
    cb.set_label("E, гр. од./мкс")
    cb.ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: fmt(v)))
    if base:
        ax.plot(*base, "ws", ms=9, mec="k", clip_on=False, zorder=5,
                label="базові значення (7; 8)")
    best_label = f"найкраща точка ({best['t1']:g}; {best['t2']:g})"
    ax.plot(best["t1"], best["t2"], "r*", ms=14, mec="k", zorder=5,
            label=best_label.replace(".", ","))
    ax.set_xlabel("Час передачі лінією 1  t1, мкс")
    ax.set_ylabel("Час передачі лінією 2  t2, мкс")
    ax.legend(loc="upper left", fontsize=9)
    finish(fig, name)


def plot_profiles(rows, name):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(6.5, 3.4), sharey=True)
    for t2, style in ((3.0, "o-"), (5.0, "s-"), (8.0, "^-")):
        sel = sorted((r for r in rows if r["t2"] == t2),
                     key=lambda r: r["t1"])
        a1.errorbar([r["t1"] for r in sel], [r["E"] for r in sel],
                    yerr=[r["E_sd"] for r in sel], fmt=style, ms=4, lw=1,
                    capsize=2, label=f"t2 = {t2:g} мкс")
    for t1, style in ((3.0, "o-"), (6.0, "s-"), (7.0, "^-")):
        sel = sorted((r for r in rows if r["t1"] == t1),
                     key=lambda r: r["t2"])
        a2.errorbar([r["t2"] for r in sel], [r["E"] for r in sel],
                    yerr=[r["E_sd"] for r in sel], fmt=style, ms=4, lw=1,
                    capsize=2, label=f"t1 = {t1:g} мкс")
    a1.set_xlabel("t1, мкс")
    a2.set_xlabel("t2, мкс")
    a1.set_ylabel("E, гр. од./мкс")
    a1.legend(fontsize=9)
    a2.legend(fontsize=9)
    finish(fig, name)


def frange(lo, hi, step):
    n = int(round((hi - lo) / step))
    return [round(lo + i * step, 2) for i in range(n + 1)]


def rounded(rows):
    return [{k: (round(v, 5) if isinstance(v, float) else v)
             for k, v in r.items()} for r in rows]


def main():
    setup_plots()
    coarse = grid_search(frange(*T1_RANGE, 0.5), frange(*T2_RANGE, 0.5))
    save_csv("optimization_coarse.csv", rounded(coarse))
    best1 = max(coarse, key=lambda r: r["E"])
    print("Етап 1:", best1)

    t1_fine = frange(max(best1["t1"] - 0.5, T1_RANGE[0]),
                     min(best1["t1"] + 0.5, T1_RANGE[1]), 0.1)
    t2_fine = frange(max(best1["t2"] - 0.5, T2_RANGE[0]),
                     min(best1["t2"] + 0.5, T2_RANGE[1]), 0.1)
    fine = grid_search(t1_fine, t2_fine)
    save_csv("optimization_fine.csv", rounded(fine))
    best2 = max(fine, key=lambda r: r["E"])
    print("Етап 2:", best2)

    keys = ("t1", "t2", "E", "E_sd")
    save_csv("optimization_summary.csv", [
        {"етап": "перебір 0,5", **{k: best1[k] for k in keys}},
        {"етап": "уточнення 0,1", **{k: best2[k] for k in keys}},
    ])
    plot_all(coarse, fine)


def plot_all(coarse, fine):
    plot_surface(coarse, max(coarse, key=lambda r: r["E"]), (7.0, 8.0),
                 "optimization_surface")
    plot_surface(fine, max(fine, key=lambda r: r["E"]), None,
                 "optimization_surface_fine")
    plot_profiles(coarse, "optimization_profiles")


def replot():
    setup_plots()

    def load(name):
        with open(RESULTS / name, encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f, delimiter=";"))
        return [{k: float(v) for k, v in r.items()} for r in rows]

    plot_all(load("optimization_coarse.csv"), load("optimization_fine.csv"))


if __name__ == "__main__":
    if "--replot" in sys.argv:
        replot()
    else:
        main()
