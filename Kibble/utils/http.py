"""
    http
    ==========

    Helpers for http views
"""

from django.utils.http import urlquote


def set_download_filename(response, name):
    """
        Set Content-Disposition in attach
    """

    response['Content-Disposition'] = 'attachment; filename="%s"; ' \
        'filename*="utf-8\'\'%s"' % (
            urlquote(name),
            urlquote(name))
