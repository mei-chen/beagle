import shutil
from django.conf import settings
from mock import patch


class PatcherMixin(object):
    patchers = {}

    def patch(self, module, name):
        self.patchers[name] = patch('%s.%s' % (module, name))
        setattr(self, name, self.patchers[name].start())
        self.addCleanup(self.patchers[name].stop)


class CleanupMixin(object):
    @classmethod
    def tearDownClass(cls):
        super(CleanupMixin, cls).tearDownClass()
        try:
            shutil.rmtree(settings.MEDIA_ROOT)
        except OSError:
            pass
