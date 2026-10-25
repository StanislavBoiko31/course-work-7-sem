from dataclasses import dataclass, replace


@dataclass(frozen=True)
class ModelParams:
    arrival_mean: tuple = (6.0, 5.0)
    arrival_sd: tuple = (1.0, 1.0)
    proc_mean: float = 2.0
    proc_half: float = 1.0
    line_time: tuple = (7.0, 8.0)

    limit: int = 3
    income: tuple = (20.0, 40.0)
    speedup_cost: tuple = (2.0, 4.0)
    base_line_time: tuple = (7.0, 8.0)

    def with_lines(self, t1, t2):
        return replace(self, line_time=(float(t1), float(t2)))

    def margin(self, k):
        speedup = self.base_line_time[k] - self.line_time[k]
        return self.income[k] - self.speedup_cost[k] * speedup
