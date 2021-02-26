def get_all_subclasses(klass):
    all_subklasses = [klass]
    current_index = 0

    while current_index < len(all_subklasses):
        all_subklasses.extend(all_subklasses[current_index].__subclasses__())
        current_index += 1

    return set(all_subklasses[1:])