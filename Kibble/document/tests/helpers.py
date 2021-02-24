# -*- coding: utf-8 -*-
import os
import tempfile

from django.test import TestCase


temp_names = []


def side_effect_tmp():
    f = tempfile.NamedTemporaryFile(delete=False)
    temp_names.append(f.name)
    return f


def side_effect_tmpfile(x, ocr=False):
    f = tempfile.NamedTemporaryFile(delete=False)
    temp_names.append(f.name)
    return f.name


class TempCleanupTestCase(TestCase):
    def tearDown(self):
        global temp_names
        while temp_names:
            n = temp_names.pop()
            if os.path.exists(n):
                os.remove(n)
