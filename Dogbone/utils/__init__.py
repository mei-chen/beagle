
def remove_extension(filename):
    chunks = filename.split('.')
    if len(chunks) <= 1:
        return filename

    return '.'.join(chunks[:-1])

