
class lazydict:
    def __init__(self, generator, **kwargs):
        self.generator = generator
        self.dict = dict(**kwargs)

    def __getitem__(self, key):
        if key not in self.dict:
            self.dict[key] = self.generator(key)
        return self.dict[key]

    def __setitem__(self, key, value):
        self.dict[key] = value
