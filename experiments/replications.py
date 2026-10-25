import csv

from switching_node import ModelParams

from .common import (RESULTS, T_MOD, T_WARMUP, mean_sd, replicate,
                     runs_needed, save_csv)

EPS = 0.01
N_PILOT = 50
POINTS = [(7.0, 8.0), (6.0, 5.0), (5.0, 5.0), (3.0, 3.0), (7.0, 3.0),
          (3.0, 8.0)]


def most_variable(n=3):
    with open(RESULTS / "pilot_sd.csv", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f, delimiter=";"))
    return [(float(r["t1"]), float(r["t2"])) for r in rows[:n]]


def main():
    rows = []
    for t1, t2 in POINTS + most_variable():
        params = ModelParams().with_lines(t1, t2)
        res = replicate(params, N_PILOT, T_MOD, T_WARMUP)
        mean, sd = mean_sd([r.profit_rate for r in res])
        rows.append({"t1": t1, "t2": t2, "E_mean": round(mean, 4),
                     "sigma": round(sd, 5), "p": runs_needed(sd, EPS)})
        print(rows[-1])
    save_csv("replications.csv", rows)
    print("Необхідна кількість прогонів:", max(r["p"] for r in rows))


if __name__ == "__main__":
    main()
