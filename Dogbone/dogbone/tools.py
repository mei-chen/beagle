from django.conf import settings


def get_http_protocol():
    try:
        return 'https' if settings.USE_HTTPS else 'http'
    except:
        return 'http'


def absolutify(url):
    """
    Make a relative url absolute
    :param url: the relative url
    :return: the absolute url
    """
    if url.startswith('http'):
        return url

    if url.startswith('//'):
        return url

    if not url.startswith('/'):
        return url

    return "%s://%s%s" % (get_http_protocol(), settings.DOMAIN, url)


class lazydict(dict):
    def __init__(self, generator, *args, **kwargs):
        super(lazydict, self).__init__(*args, **kwargs)
        self.generator = generator

    def __getitem__(self, key):
        if key not in self:
            super(lazydict, self).__setitem__(key, self.generator(key))
        return super(lazydict, self).__getitem__(key)
