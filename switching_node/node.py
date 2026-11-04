import itertools
from dataclasses import dataclass

from .distributions import FunRand
from .elements import (Create, Dispose, Process, RouteBlocking,
                       Synchronization)
from .params import ModelParams

DIRECTIONS = (0, 1)


@dataclass
class Results:
    t_obs: float
    n_in: tuple
    n_fail: tuple
    n_out: tuple
    p_fail: tuple
    throughput: tuple
    util_proc: float
    util_line: tuple
    mean_q0: float
    mean_qline: tuple
    sojourn_mean: tuple
    profit_rate: float


class SwitchingNodeModel:
    def __init__(self, params=ModelParams(), seed=1, protocol=None,
                 keep_sojourn=False):
        p = self.p = params
        rand = [FunRand(seed * 100 + i) for i in range(4)]
        ids = itertools.count(1)
        self.exits = [Dispose(f"N{k + 1}", keep_sojourn)
                      for k in DIRECTIONS]
        self.lines = [Process(f"L{k + 1}", lambda k=k: p.line_time[k],
                              self.exits[k],
                              f"кінець передачі #{{id}} лінією {k + 1}")
                      for k in DIRECTIONS]
        self.sync = Synchronization(
            "BP", lambda: self.processors[0].busy
            + self.processors[1].busy == 1)
        self.processors = [
            Process(f"P{k + 1}",
                    lambda: rand[2].unif(p.proc_mean, p.proc_half),
                    self.lines[k], f"кінець обробки #{{id}} у P{k + 1}",
                    self.sync)
            for k in DIRECTIONS]
        self.blocking = [
            RouteBlocking(f"B{k + 1}",
                          lambda k=k: self.in_node(k) == p.limit)
            for k in DIRECTIONS]
        self.sources = [
            Create(f"Надходження {k + 1}", k,
                   lambda k=k: rand[k].norm(p.arrival_mean[k],
                                            p.arrival_sd[k]),
                   self.blocking[k], self.processors[k], ids)
            for k in DIRECTIONS]
        self.timed = [*self.sources, *self.processors, *self.lines]
        self.stat = [*self.processors, *self.lines]
        self.order = rand[3]
        self.protocol = protocol
        self.t = 0.0
        self.t_start = 0.0

    def in_node(self, k):
        P, L = self.processors[k], self.lines[k]
        return len(P.queue) + P.busy + len(L.queue) + L.busy

    def simulate(self, t_mod, t_warmup=0.0):
        self.run(t_warmup)
        self._reset_stats()
        self.run(t_mod)
        return self.results()

    def run(self, t_end):
        while True:
            t_next = min([e.tnext for e in self.timed])
            if t_next > t_end:
                self._advance(t_end)
                return
            self._advance(t_next)

            events = [e for e in self.timed if e.tnext == t_next]
            if len(events) > 1:
                self.order.shuffle(events)
            for e in events:
                text = e.out_act(self.t)
                if self.protocol:
                    self.protocol(self.record(text))

    def _advance(self, t_next):
        dt = t_next - self.t
        if dt > 0.0:
            for e in self.stat:
                e.do_statistics(dt)
        self.t = t_next

    def _reset_stats(self):
        self.t_start = self.t
        for e in [*self.sources, *self.stat, *self.exits]:
            e.reset_stats()

    def results(self):
        T = self.t - self.t_start
        n_in = tuple(s.n_in for s in self.sources)
        n_fail = tuple(s.n_fail for s in self.sources)
        n_out = tuple(x.n_out for x in self.exits)
        profit = sum(n_out[k] * self.p.margin(k) for k in DIRECTIONS)
        return Results(
            t_obs=T, n_in=n_in, n_fail=n_fail, n_out=n_out,
            p_fail=tuple(f / n if n else 0.0 for f, n in zip(n_fail, n_in)),
            throughput=tuple(n / T for n in n_out),
            util_proc=sum(e.busy_time for e in self.processors) / T,
            util_line=tuple(e.busy_time / T for e in self.lines),
            mean_q0=sum(e.queue_time for e in self.processors) / T,
            mean_qline=tuple(e.queue_time / T for e in self.lines),
            sojourn_mean=tuple((x.sum_out - x.sum_in) / x.n_out
                               if x.n_out else 0.0 for x in self.exits),
            profit_rate=profit / T,
        )

    def record(self, text):
        def busy(e):
            return f"#{e.current.id}" if e.current else "-"

        p1, p2 = self.processors
        l1, l2 = self.lines
        return {
            "t": self.t, "event": text,
            "Q01": len(p1.queue), "P1": busy(p1),
            "Q02": len(p2.queue), "P2": busy(p2),
            "Q1": len(l1.queue), "L1": busy(l1),
            "Q2": len(l2.queue), "L2": busy(l2),
            "n": tuple(self.in_node(k) for k in DIRECTIONS),
            "B": tuple(int(b.blocked) for b in self.blocking),
            "N_in": tuple(s.n_in for s in self.sources),
            "N_fail": tuple(s.n_fail for s in self.sources),
            "N_out": tuple(x.n_out for x in self.exits),
        }

    def snapshot(self):
        profit = sum(self.exits[k].n_out * self.p.margin(k)
                     for k in DIRECTIONS)
        return {"t": self.t, "profit_rate": profit / (self.t - self.t_start),
                "in_system": tuple(self.in_node(k) for k in DIRECTIONS)}


def format_record(r):
    return (f"{r['t']:9.3f} | {r['event']:<30} | "
            f"Q01={r['Q01']} P1={r['P1']:<5} "
            f"Q02={r['Q02']} P2={r['P2']:<5} | "
            f"Q1={r['Q1']} L1={r['L1']:<5} | Q2={r['Q2']} L2={r['L2']:<5} | "
            f"n={r['n'][0]},{r['n'][1]} B={r['B'][0]},{r['B'][1]} | "
            f"вх={r['N_in'][0]},{r['N_in'][1]} "
            f"відм={r['N_fail'][0]},{r['N_fail'][1]} "
            f"перед={r['N_out'][0]},{r['N_out'][1]}")
