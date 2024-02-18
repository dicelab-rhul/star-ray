class _History:
    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.buffer = []

    def __len__(self):
        return len(self.buffer)

    def push(self, item):
        self.buffer.append(item)

    def __getitem__(self, index: int | slice):
        return self.buffer[index]

    def close(self):
        pass
