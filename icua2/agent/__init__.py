import uuid

__all__ = ("Identifiable", "Agent")


class Identifiable:
    def __init__(self):
        super().__init__()
        self.__id__ = str(uuid.uuid4())
        print(self.__id__)

    @property
    def id(self):
        return self.__id__


class Agent(Identifiable):
    def __init__(self):
        super().__init__()
