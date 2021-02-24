class Enum(object):
    """
    Examples:
        >>> enum = Enum(CAT=3, DOG=9)
        >>> enum.CAT
        >>> 3
        >>> enum[9]
        >>> 'DOG'
        >>> enum = Enum('CAT', 'DOG')
        >>> enum.CAT
        >>> 0
    """

    def __init__(self, *args, **kwargs):
        if args and kwargs:
            raise Exception('Position or keyword arguments only.')
        if args and isinstance(args[0], (tuple, list)):
            args = args[0]
        for index, constant in enumerate(args):
            setattr(self, constant, index)
        for constant, index in kwargs.items():
            setattr(self, constant, index)

    def __getitem__(self, item):
        reverse_dict = {k: v for v, k in self.__dict__.items()}
        try:
            return reverse_dict[item]
        except KeyError:
            raise StopIteration

    def enumerate(self):
        return tuple(enumerate(self))
