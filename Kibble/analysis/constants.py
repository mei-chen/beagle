from enum import Enum


class ReportTypes(Enum):
    RegEx = 0
    KeyWord = 1
    SentSim = 2

    @classmethod
    def choices(cls):
        return tuple((x.value, x.name) for x in cls)
