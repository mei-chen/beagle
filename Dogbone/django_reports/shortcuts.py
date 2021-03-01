import logging

from django.utils.importlib import import_module


def init_report(module_name, class_name):
    try:
        module = import_module(module_name)
        ReportClass = getattr(module, class_name)
        report = ReportClass()
        return report
    except Exception as e:
        logging.error('Report %s.%s could not be loaded error=%s' % (module_name, class_name, str(e)))