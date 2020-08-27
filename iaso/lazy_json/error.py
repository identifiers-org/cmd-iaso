class JSONLazyDecodeError(ValueError):
    def __init__(self, msg, pos):
        ValueError.__init__(self, "%s: char %d" % (msg, pos))

        self.msg = msg
        self.pos = pos
