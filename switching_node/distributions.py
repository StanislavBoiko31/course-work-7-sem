import math
import random


class FunRand:
    def __init__(self, seed=None):
        self.rng = random.Random(seed)
        self._spare = None

    def unif(self, d, s):
        return d - s + 2.0 * s * self.rng.random()

    def norm(self, d, s):
        while True:
            if self._spare is None:
                r1 = 1.0 - self.rng.random()
                r2 = self.rng.random()
                radius = math.sqrt(-2.0 * math.log(r1))
                z = radius * math.cos(2.0 * math.pi * r2)
                self._spare = radius * math.sin(2.0 * math.pi * r2)
            else:
                z, self._spare = self._spare, None
            x = d + s * z
            if x > 0.0:
                return x

    def shuffle(self, items):
        self.rng.shuffle(items)
