import argparse

from switching_node import ModelParams, SwitchingNodeModel, format_record


def print_results(r):
    print(f"Час спостереження: {r.t_obs:.0f} мкс")
    for k in (0, 1):
        print(f"Напрям {k + 1}: надійшло {r.n_in[k]}, "
              f"відмов {r.n_fail[k]} (P = {r.p_fail[k]:.4f}), "
              f"передано {r.n_out[k]} (λ = {r.throughput[k]:.4f} 1/мкс)")
        print(f"  лінія {k + 1}: завантаження {r.util_line[k]:.4f}, "
              f"середня черга {r.mean_qline[k]:.3f}")
        print(f"  час у вузлі {r.sojourn_mean[k]:.2f} ± "
              f"{r.sojourn_sd[k]:.2f} мкс "
              f"[{r.sojourn_min[k]:.2f}; {r.sojourn_max[k]:.2f}]")
    print(f"Процесор: завантаження {r.util_proc:.4f}, "
          f"середня черга {r.mean_q0:.3f}")
    print(f"Економічна ефективність {r.profit_rate:.4f} гр. од./мкс")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--t-mod", type=float, default=10000.0)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--t1", type=float, default=7.0)
    ap.add_argument("--t2", type=float, default=8.0)
    ap.add_argument("--protocol", type=int, default=40,
                    help="скільки перших подій вивести")
    args = ap.parse_args()

    shown = []

    def protocol(record):
        if len(shown) < args.protocol:
            shown.append(record)
            print(format_record(record))

    params = ModelParams().with_lines(args.t1, args.t2)
    model = SwitchingNodeModel(params, seed=args.seed, protocol=protocol)
    print_results(model.simulate(args.t_mod))


if __name__ == "__main__":
    main()
