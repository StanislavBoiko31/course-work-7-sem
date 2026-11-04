import math
from collections import deque
from dataclasses import dataclass

INF = math.inf


@dataclass
class Message:
    id: int
    t_enter: float


class Element:
    def __init__(self, name):
        self.name = name
        self.tnext = INF

    def out_act(self, t):
        raise NotImplementedError

    def do_statistics(self, dt):
        pass

    def reset_stats(self):
        pass


class RouteBlocking(Element):
    def __init__(self, name, condition):
        super().__init__(name)
        self.condition = condition

    @property
    def blocked(self):
        return self.condition()


class Synchronization(RouteBlocking):
    def __init__(self, name, condition):
        super().__init__(name, condition)
        self.devices = []

    def start_next(self, t):
        waiting = [d for d in self.devices if d.queue]
        if waiting:
            d = min(waiting, key=lambda d: d.queue[0].id)
            d.start(d.queue.popleft(), t)


class Create(Element):
    def __init__(self, name, direction, delay, blocking, next_element,
                 ids):
        super().__init__(name)
        self.direction = direction
        self.delay = delay
        self.blocking = blocking
        self.next_element = next_element
        self.ids = ids
        self.tnext = delay()
        self.reset_stats()

    def reset_stats(self):
        self.n_in = 0
        self.n_fail = 0

    def out_act(self, t):
        self.tnext = t + self.delay()
        self.n_in += 1
        k = self.direction + 1
        if self.blocking.blocked:
            self.n_fail += 1
            return f"надходження н{k}: відмова"
        msg = Message(next(self.ids), t)
        self.next_element.in_act(msg, t)
        return f"надходження н{k}: #{msg.id}"


class Process(Element):
    def __init__(self, name, delay, next_element, event, sync=None):
        super().__init__(name)
        self.delay = delay
        self.next_element = next_element
        self.event = event
        self.sync = sync
        if sync:
            sync.devices.append(self)
        self.queue = deque()
        self.current = None
        self.reset_stats()

    def reset_stats(self):
        self.busy_time = 0.0
        self.queue_time = 0.0

    @property
    def busy(self):
        return int(self.current is not None)

    def in_act(self, msg, t):
        blocked = self.sync.blocked if self.sync else self.busy
        if blocked:
            self.queue.append(msg)
        else:
            self.start(msg, t)

    def out_act(self, t):
        msg = self.current
        self.current = None
        self.tnext = INF
        if self.sync:
            self.sync.start_next(t)
        elif self.queue:
            self.start(self.queue.popleft(), t)
        self.next_element.in_act(msg, t)
        return self.event.format(id=msg.id)

    def start(self, msg, t):
        self.current = msg
        self.tnext = t + self.delay()

    def do_statistics(self, dt):
        self.busy_time += self.busy * dt
        self.queue_time += len(self.queue) * dt


class Dispose(Element):
    def __init__(self, name, keep_values=False):
        super().__init__(name)
        self.keep_values = keep_values
        self.reset_stats()

    def reset_stats(self):
        self.n_out = 0
        self.sum_in = 0.0
        self.sum_out = 0.0
        self.values = []

    def in_act(self, msg, t):
        self.n_out += 1
        self.sum_in += msg.t_enter
        self.sum_out += t
        if self.keep_values:
            self.values.append(t - msg.t_enter)
