# -*- coding: utf-8 -*-
from unittest import TestCase

from clauses_statistics.models import ClausesStatistic


class ClausesStatisticTest(TestCase):

    def test_todict(self):
        stat = ClausesStatistic(tag='tag', avg_word_count=99)

        self.assertEqual(stat.to_dict(),
                         {'tag': 'tag', 'avg_word_count': 99})

    def test_no_avg_word_count_given(self):
        incomp_stat = ClausesStatistic(tag='tag_incomp')

        self.assertEqual(incomp_stat.to_dict(),
                         {'tag': 'tag_incomp', 'avg_word_count': False})

    def test_avg_word_count(self):
        stat1 = ClausesStatistic(tag='tag1')
        stat1.set_avgwordcount(['1 2', '1 2 3', '1 2   3  4'])
        
        self.assertEqual(stat1.avg_word_count, 3)
