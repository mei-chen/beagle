def hide_exceptions(return_f):
    def hide_exceptions_decorator(function):
        def decorated_function(*args, **kwargs):
            try:
                return function(*args, **kwargs)
            except Exception as e:
                return return_f(e)

        return decorated_function
    return hide_exceptions_decorator


def first(iterable, predicate=None, default=None):
    """
    Return the first item in `iterable` that satisfies `predicate`
    If none is found, return `default`
    :param iterable: iterable collection
    :param predicate: the condition that needs to be satisfied
    :param default: the default return value if nothing good is found
    :return:
    """
    if predicate is None:
        predicate = lambda x: x

    for item in iterable:
        if predicate(item):
            return item

    return default