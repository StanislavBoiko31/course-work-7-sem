import csv
import math

import matplotlib.pyplot as plt

from switching_node import ModelParams, SwitchingNodeModel

from .common import (RESULTS, T_MOD, T_WARMUP, finish, mean_sd, replicate,
                     save_csv, setup_plots)

N_TRIAL = 200
BASE = ModelParams()


def optimum():
    with open(RESULTS / "optimization_summary.csv", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f, delimiter=";"))
    return round(float(rows[1]["t1"]), 1), round(float(rows[1]["t2"]), 1)


def fmt(t1, t2):
    return f"({t1:g}; {t2:g})".replace(".", ",")


T1_OPT, T2_OPT = optimum()
VARIANTS = [
    ("базовий (7; 8)", BASE),
    (f"прискорено лише лінію 1 {fmt(T1_OPT, 8)}",
     BASE.with_lines(T1_OPT, 8.0)),
    (f"прискорено лише лінію 2 {fmt(7, T2_OPT)}",
     BASE.with_lines(7.0, T2_OPT)),
    (f"оптимум {fmt(T1_OPT, T2_OPT)}", BASE.with_lines(T1_OPT, T2_OPT)),
]
LIMIT_4 = ("оптимум + обмеження 4",
           ModelParams(line_time=(T1_OPT, T2_OPT), limit=4))


def summarize(name, params):
    res = replicate(params, N_TRIAL, T_MOD, T_WARMUP)
    e, sd = mean_sd([r.profit_rate for r in res])

    def avg(f, digits=6):
        return round(sum(f(r) for r in res) / len(res), digits)

    lam = (avg(lambda r: r.throughput[0], 6),
           avg(lambda r: r.throughput[1], 6))
    income = sum(lam[k] * params.income[k] for k in (0, 1))
    return {
        "варіант": name, "t1": params.line_time[0],
        "t2": params.line_time[1], "limit": params.limit,
        "E": round(e, 6), "eps": round(sd * math.sqrt(20 / N_TRIAL), 6),
        "дохід": round(income, 6), "витрати": round(income - e, 6),
        "λ1": lam[0], "λ2": lam[1],
        "P1": avg(lambda r: r.p_fail[0]), "P2": avg(lambda r: r.p_fail[1]),
        "ρL1": avg(lambda r: r.util_line[0]),
        "ρL2": avg(lambda r: r.util_line[1]),
        "ρP": avg(lambda r: r.util_proc),
        "L0": avg(lambda r: r.mean_q0),
        "L1": avg(lambda r: r.mean_qline[0]),
        "L2": avg(lambda r: r.mean_qline[1]),
        "W1": avg(lambda r: r.sojourn_mean[0]),
        "W2": avg(lambda r: r.sojourn_mean[1]),
        "sW1": avg(lambda r: r.sojourn_sd[0]),
        "sW2": avg(lambda r: r.sojourn_sd[1]),
    }


def sojourn_histograms():
    fig, axes = plt.subplots(1, 2, figsize=(6.5, 3.2), sharey=True)
    rows = []
    for (name, params), color in ((VARIANTS[0], "tab:gray"),
                                  (VARIANTS[3], "tab:green")):
        model = SwitchingNodeModel(params, seed=1)
        r = model.simulate(T_MOD * 5, T_WARMUP)
        for k, ax in enumerate(axes):
            values = model.exits[k].sojourn
            ax.hist(values, bins=40, range=(0, 30), density=True,
                    alpha=0.6, color=color, label=name)
            rows.append({"варіант": name, "напрям": k + 1,
                         "n": len(values),
                         "середнє": round(r.sojourn_mean[k], 3),
                         "СКВ": round(r.sojourn_sd[k], 3),
                         "min": round(r.sojourn_min[k], 3),
                         "max": round(r.sojourn_max[k], 3)})
    for k, ax in enumerate(axes):
        ax.set_title(f"Напрям {k + 1}")
        ax.set_xlabel("Час перебування у вузлі, мкс")
    axes[0].set_ylabel("Щільність відносних частот, 1/мкс")
    axes[1].legend(fontsize=9, loc="upper left")
    finish(fig, "sojourn_hist")
    save_csv("sojourn_stats.csv", rows)


def main():
    setup_plots()
    rows = []
    for name, params in VARIANTS:
        rows.append(summarize(name, params))
        print(rows[-1], flush=True)
    save_csv("proposals.csv", rows)
    row = summarize(*LIMIT_4)
    print(row, flush=True)
    save_csv("proposals_limit4.csv", [row])
    sojourn_histograms()


if __name__ == "__main__":
    main()
