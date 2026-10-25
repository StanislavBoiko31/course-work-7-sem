from switching_node import ModelParams, SwitchingNodeModel, format_record

from .common import save_csv

T_VERIFY = 10000.0
SEED = 1

BASE = ModelParams()
CASES = [
    ("базові значення", BASE),
    ("a1 = 12 (потік 1 рідший)", ModelParams(arrival_mean=(12.0, 5.0))),
    ("a2 = 10 (потік 2 рідший)", ModelParams(arrival_mean=(6.0, 10.0))),
    ("s1 = s2 = 0 (детерміновані потоки)",
     ModelParams(arrival_sd=(0.0, 0.0))),
    ("обробка unif(4, 1)", ModelParams(proc_mean=4.0)),
    ("t1 = 3 (швидка лінія 1)", BASE.with_lines(3, 8)),
    ("t2 = 3 (швидка лінія 2)", BASE.with_lines(7, 3)),
    ("t1 = t2 = 12", BASE.with_lines(12, 12)),
    ("обмеження 1", ModelParams(limit=1)),
    ("обмеження 100", ModelParams(limit=100)),
    ("усе детерміноване, t1 = t2 = 3",
     ModelParams(arrival_sd=(0.0, 0.0), proc_half=0.0,
                 line_time=(3.0, 3.0))),
]


def verification_table():
    rows = []
    for i, (name, params) in enumerate(CASES, start=1):
        r = SwitchingNodeModel(params, seed=SEED).simulate(T_VERIFY)
        rows.append({
            "№": i, "зміна": name,
            "λ1": round(r.throughput[0], 4), "λ2": round(r.throughput[1], 4),
            "P1": round(r.p_fail[0], 4), "P2": round(r.p_fail[1], 4),
            "ρP": round(r.util_proc, 4),
            "ρL1": round(r.util_line[0], 4), "ρL2": round(r.util_line[1], 4),
            "L0": round(r.mean_q0, 3),
            "L1": round(r.mean_qline[0], 3), "L2": round(r.mean_qline[1], 3),
            "W1": round(r.sojourn_mean[0], 2),
            "W2": round(r.sojourn_mean[1], 2),
            "E": round(r.profit_rate, 4),
        })
        print(rows[-1])
    save_csv("verification.csv", rows)


def protocol_fragment(params, name, n_events, t_mod):
    records = []

    def keep(rec):
        if len(records) < n_events:
            records.append(rec)

    SwitchingNodeModel(params, seed=SEED, protocol=keep).simulate(t_mod)
    rows = [{
        "t": f"{r['t']:.3f}", "подія": r["event"], "Q0": r["Q0"],
        "P": r["P"], "Q1": r["Q1"], "L1": r["L1"], "Q2": r["Q2"],
        "L2": r["L2"], "n1": r["n"][0], "n2": r["n"][1],
        "B1": r["B"][0], "B2": r["B"][1],
        "вх": f"{r['N_in'][0]}/{r['N_in'][1]}",
        "відм": f"{r['N_fail'][0]}/{r['N_fail'][1]}",
        "перед": f"{r['N_out'][0]}/{r['N_out'][1]}",
    } for r in records]
    save_csv(name, rows)
    for r in records:
        print(format_record(r))


if __name__ == "__main__":
    verification_table()
    protocol_fragment(BASE, "protocol_base.csv", 45, 200.0)
    protocol_fragment(CASES[-1][1], "protocol_simultaneous.csv", 30, 60.0)
