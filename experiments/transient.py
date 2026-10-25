from itertools import combinations

import matplotlib.pyplot as plt

from switching_node import ModelParams, SwitchingNodeModel

from .common import finish, mean_sd, save_csv, setup_plots
from .optimization import T1_RANGE, T2_RANGE, frange

EPS = 0.05
N_PILOT = 20
T_PILOT = 20000.0
T_LONG = 60000.0
STEP = 10.0
N_TRIAL = 5
N_ENSEMBLE = 500
T_WARMUP = 200.0


def pilot():
    rows = []
    for t1 in frange(*T1_RANGE, 0.5):
        for t2 in frange(*T2_RANGE, 0.5):
            params = ModelParams().with_lines(t1, t2)
            e, sd = mean_sd([SwitchingNodeModel(params, seed=seed)
                             .simulate(T_PILOT, T_WARMUP).profit_rate
                             for seed in range(1, N_PILOT + 1)])
            rows.append({"t1": t1, "t2": t2, "E": round(e, 4),
                         "sigma": round(sd, 5)})
    rows.sort(key=lambda r: -r["sigma"])
    save_csv("pilot_sd.csv", rows)
    for r in rows[:5]:
        print("пілот:", r)
    return [(r["t1"], r["t2"]) for r in rows]


def trajectory(model, t_mod, step, t_warmup=0.0):
    if t_warmup:
        model.run(t_warmup)
        model._reset_stats()
    traj = []
    for i in range(1, round((t_mod - t_warmup) / step) + 1):
        model.run(t_warmup + i * step)
        traj.append(model.snapshot())
    return traj


def trajectories(params, n_runs, t_mod, step, t_warmup=0.0):
    return [trajectory(SwitchingNodeModel(params, seed=seed), t_mod, step,
                       t_warmup)
            for seed in range(1, n_runs + 1)]


def settle_time(trajs, eps):
    n_points = len(trajs[0])
    settle = trajs[0][0]["t"]
    for idx in range(n_points):
        values = [tr[idx]["profit_rate"] for tr in trajs]
        spread = max(abs(a - b) for a, b in combinations(values, 2))
        if spread >= eps:
            if idx + 1 < n_points:
                settle = trajs[0][idx + 1]["t"]
            else:
                settle = float("inf")
    return settle


def ensemble_in_system(params, n_runs, t_mod, step):
    sums = None
    for seed in range(1, n_runs + 1):
        traj = trajectory(SwitchingNodeModel(params, seed=1000 + seed),
                          t_mod, step)
        n = [sum(s["in_system"]) for s in traj]
        sums = n if sums is None else [a + b for a, b in zip(sums, n)]
    return [(traj[i]["t"], sums[i] / n_runs) for i in range(len(sums))]


def label(t1, t2):
    return f"t1 = {t1:g} мкс, t2 = {t2:g} мкс".replace(".", ",")


def settle_row(t1, t2, trajs, T):
    row = {"t1": t1, "t2": t2, "T_settle": T}
    for t in (20000, 40000):
        v = [tr[round((t - T_WARMUP) / STEP) - 1]["profit_rate"]
             for tr in trajs]
        row[f"spread_{t}"] = round(max(v) - min(v), 4)
    return row


def plot_cumulative(points, extra):
    rows = []
    fig, axes = plt.subplots(len(points), 1, figsize=(6.5, 6.8),
                             sharex=True)
    for ax, (t1, t2) in zip(axes, points):
        params = ModelParams().with_lines(t1, t2)
        trajs = trajectories(params, N_TRIAL, T_LONG, STEP, T_WARMUP)
        T = settle_time(trajs, EPS)
        final = [tr[-1]["profit_rate"] for tr in trajs]
        rows.append(settle_row(t1, t2, trajs, T))
        print(rows[-1])
        for i, tr in enumerate(trajs, start=1):
            ax.plot([s["t"] for s in tr], [s["profit_rate"] for s in tr],
                    lw=0.9, label=f"прогін {i}")
        mid = sum(final) / len(final)
        ax.set_ylim(mid - 0.6, mid + 0.6)
        ax.axvline(T, color="k", ls="--", lw=1)
        ax.text(T, mid + 0.42, f" T = {T:.0f} мкс ", fontsize=11,
                ha="right" if T > 0.7 * T_LONG else "left")
        ax.set_title(label(t1, t2))
        ax.set_ylabel("E(t), гр. од./мкс")
    axes[-1].set_xlabel("Модельний час t, мкс")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, ncol=5, loc="lower center", fontsize=10,
               bbox_to_anchor=(0.5, -0.03))
    finish(fig, "transient_cumulative")
    for t1, t2 in extra:
        trajs = trajectories(ModelParams().with_lines(t1, t2), N_TRIAL,
                             T_LONG, STEP, T_WARMUP)
        rows.append(settle_row(t1, t2, trajs, settle_time(trajs, EPS)))
        print(rows[-1])
    save_csv("transient_settle.csv", rows)
    t_max = max(r["T_settle"] for r in rows)
    print(f"найбільше T = {t_max:.0f} мкс -> T_mod = "
          f"{-(-t_max // 10000) * 10000:.0f} мкс")


def plot_ensemble(points):
    fig, ax = plt.subplots(figsize=(6.5, 3.6))
    rows = []
    for t1, t2 in points:
        params = ModelParams().with_lines(t1, t2)
        ens = ensemble_in_system(params, N_ENSEMBLE, 400.0, 2.0)
        rows += [{"t1": t1, "t2": t2, "t": t, "n": round(v, 4)}
                 for t, v in ens]
        ax.plot([t for t, _ in ens], [v for _, v in ens], lw=1.2,
                label=label(t1, t2))
    save_csv("transient_ensemble.csv", rows)
    ax.axvline(T_WARMUP, color="k", ls="--", lw=1)
    ax.text(T_WARMUP, 0.4, "  відкинутий інтервал 200 мкс", fontsize=11)
    ax.set_xlabel("Модельний час t, мкс")
    ax.set_ylabel("Середня кількість повідомлень у вузлі")
    ax.legend(loc="center right")
    finish(fig, "transient_ensemble")


def main():
    setup_plots()
    plot_ensemble([(7.0, 8.0), (6.0, 4.5), (3.0, 3.0)])
    ranked = pilot()
    plot_cumulative([(7.0, 8.0), ranked[0], (3.0, 3.0)], ranked[1:3])


if __name__ == "__main__":
    main()
