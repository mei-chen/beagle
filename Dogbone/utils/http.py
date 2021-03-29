import urllib.parse


def filename_from_url(url, default_filename=None, default_extension=None):
    """
    Extract a file name from a given url
    Examples:
        - `http://example.com/agreement.docx` => `agreement.docx`
        - `http://example.com/file` => `file`
        - `http://example.com/file` with `default_extension`=='txt' => `file.txt`

    :param url: `http://example.com/agreement.docx` => `agreement.docx`
    :param default_filename: In case a filename can't be extract, default to this (can be a function as well)
    :param default_extension: In case the document doesn't have an extension, add this default one
    :return: The file name
    """
    path = urllib.parse.urlsplit(url).path

    if path is None:
        return default_filename if not callable(default_filename) else str(default_filename())

    filename = path.split('/')[-1]

    if not filename:
        return default_filename if not callable(default_filename) else str(default_filename())

    if '.' not in filename and default_extension:
        return '%s.%s' % (filename, default_extension)

    return filename