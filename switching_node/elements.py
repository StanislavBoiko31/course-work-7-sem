import math
from collections import deque
from dataclasses import dataclass

INF = math.inf


@dataclass
class Message:
    id: int
    direction: int
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
    def __init__(self, name, limit):
        super().__init__(name)
        self.limit = limit
        self.n = 0

    @property
    def blocked(self):
        return self.n >= self.limit


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
        msg = Message(next(self.ids), self.direction, t)
        self.blocking.n += 1
        self.next_element.in_act(msg, t)
        return f"надходження н{k}: #{msg.id}"


class Process(Element):
    def __init__(self, name, delay, route, event):
        super().__init__(name)
        self.delay = delay
        self.route = route
        self.event = event
        self.queue = deque()
        self.current = None
        self.reset_stats()

    def reset_stats(self):
        self.busy_time = 0.0
        self.queue_time = 0.0

    def in_act(self, msg, t):
        if self.current is None:
            self._start(msg, t)
        else:
            self.queue.append(msg)

    def out_act(self, t):
        msg = self.current
        self.current = None
        self.tnext = INF
        if self.queue:
            self._start(self.queue.popleft(), t)
        self.route(msg).in_act(msg, t)
        return self.event.format(id=msg.id, k=msg.direction + 1)

    def _start(self, msg, t):
        self.current = msg
        self.tnext = t + self.delay()

    def do_statistics(self, dt):
        if self.current is not None:
            self.busy_time += dt
        self.queue_time += len(self.queue) * dt


class Dispose(Element):
    def __init__(self, name, blocking):
        super().__init__(name)
        self.blocking = blocking
        self.reset_stats()

    def reset_stats(self):
        self.sojourn = []

    def in_act(self, msg, t):
        self.blocking.n -= 1
        self.sojourn.append(t - msg.t_enter)
