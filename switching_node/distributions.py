import random


class FunRand:
    def __init__(self, seed=None):
        self.rng = random.Random(seed)

    def unif(self, d, s):
        return self.rng.uniform(d - s, d + s)

    def norm(self, d, s):
        while True:
            x = self.rng.gauss(d, s)
            if x > 0.0:
                return x

    def shuffle(self, items):
        self.rng.shuffle(items)
