from .value import LazyValue


class LazyObject:
    def __init__(self, string, decoder, generator, start):
        self.__string = string
        self.__decoder = decoder
        self.__generator = generator
        self.__indices = dict()
        self.__start = start
        self.__end = None

    def __getitem__(self, key):
        while self.__generator is not None and key not in self.__indices:
            try:
                nkey, value = next(self.__generator)

                self.__indices[nkey] = value
            except StopIteration as err:
                self.__generator = None
                self.__end = err.value[1]

        obj = self.__indices[key]

        if obj.value == obj or obj.value is None:
            res = self.__decoder.lazy_decode(self.__string, idx=obj.start)
        else:
            res = obj

        return res.value

    def __len__(self):
        # TODO: Should this require parsing everything?

        return len(self.__indices)

    def get(self, key, default=None):
        try:
            return self.__getitem__(key)
        except KeyError:
            return default

    def keys(self):
        # TODO: Should this require parsing everything?

        return self.__indices.keys()

    def __repr__(self):
        content = ", ".join(f'"{key}": ...' for key in self.keys())

        if self.__generator is not None:
            if len(content) > 0:
                content += ", ..."
            else:
                content = "..."

        return f"LazyObject({{{content}}})"

    def into(self):
        _ = self.end

        return LazyValue(
            {k: v.value for k, v in self.__indices.items()}, self.__start, self.__end
        )

    @property
    def value(self):
        return self

    @property
    def start(self):
        return self.__start

    @property
    def end(self):
        while self.__generator is not None:
            try:
                nkey, value = next(self.__generator)

                self.__indices[nkey] = value
            except StopIteration as err:
                self.__generator = None
                self.__end = err.value[1]

        return self.__end
