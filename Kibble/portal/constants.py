from enum import Enum


class ProjectStatus(Enum):
    Active = 0
    Inactive = 1
    Archived = 2

    @classmethod
    def choices(cls):
        return tuple((x.value, x.name) for x in cls)
