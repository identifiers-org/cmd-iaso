from .value import LazyValue


class LazyArray:
    def __init__(self, string, decoder, generator, start):
        self.__string = string
        self.__decoder = decoder
        self.__generator = generator
        self.__indices = []
        self.__start = start
        self.__end = None

    def __getitem__(self, index):
        if self.__generator is not None and index <= len(self):
            pass

        while self.__generator is not None and index >= len(self):
            try:
                value = next(self.__generator)

                self.__indices.append(value)
            except StopIteration as err:
                self.__generator = None
                self.__end = err.value[1]

        obj = self.__indices[index]

        if obj.value == obj or obj.value is None:
            res = self.__decoder.lazy_decode(self.__string, idx=obj.start)
        else:
            res = obj

        return res.value

    def __len__(self):
        # TODO: Should this require parsing everything?

        return len(self.__indices)

    def __repr__(self):
        content = ", ".join("..." for _ in range(len(self)))

        if self.__generator is not None:
            if len(content) > 0:
                content += ", ..."
            else:
                content = "..."

        return f"LazyArray([{content}])"

    def into(self):
        _ = self.end

        return LazyValue([v.value for v in self.__indices], self.__start, self.__end)

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
                value = next(self.__generator)

                self.__indices.append(value)
            except StopIteration as err:
                self.__generator = None
                self.__end = err.value[1]

        return self.__end
