import logging
import inspect


def autodiscover():
    """
    Auto-discover INSTALLED_APPS reports.py modules and fail silently when
    not present.
    """

    from django.conf import settings
    from importlib import import_module
    from django.utils.module_loading import module_has_submodule

    for app in settings.INSTALLED_APPS:
        mod = import_module(app)
        # Attempt to import the app's report module.
        try:
            import_module('%s.reports' % app)
            logging.info('Imported %s.reports.py file' % app)
        except:
            # Decide whether to bubble up this error. If the app just
            # doesn't have an reports module, we can ignore the error
            # attempting to import it, otherwise we want it to bubble up.
            if module_has_submodule(mod, 'reports'):
                raise


class Report(object):

    form_class = None
    description = 'Basic Report class'
    class_name = classmethod(lambda cls: cls.__name__)
    module_name = classmethod(lambda cls: inspect.getmodule(cls).__name__)

    @classmethod
    def all(cls):
        return cls.__subclasses__()

    def __init__(self):
        if self.__class__.form_class is not None:
            self.form = self.__class__.form_class()
        else:
            self.form = None

    @property
    def params(self):
        if self.form is not None:
            return self.form.data
        return {}

    def bind(self, request):
        """
        Bind the form to **kwargs
        """
        if self.__class__.form_class is not None:
            self.form = self.__class__.form_class(request.POST)
        else:
            self.form = None

    def is_valid(self):
        if self.__class__.form_class is not None:
            return self.form.is_valid
        return True

    def generate(self, **kwargs):
        """
        Should yield one line at a time
        """
        raise NotImplemented('Please override this in every report')
