class LazyValue:
    def __init__(self, value, start, end):
        self.__value = value
        self.__start = start
        self.__end = end

    def __repr__(self):
        content = ", ".join("..." for _ in range(len(self)))

        if self.__generator is not None:
            if len(content) > 0:
                content += ", ..."
            else:
                content = "..."

        return f"LazyValue({self.__value if self.__value is not None else '...'})"

    @property
    def value(self):
        return self.__value

    @property
    def start(self):
        return self.__start

    @property
    def end(self):
        return self.__end
