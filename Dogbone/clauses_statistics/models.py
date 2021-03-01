from django.db import models
from model_utils.models import TimeStampedModel


class ClausesStatistic(TimeStampedModel):
    """
    Holds statistics (numbers) about the clauses from pre-trained classifiers'
    training sets. These are pre-computed at an initialization time and are
    statically stored in the db (not updated as users put new contracts in).
    """

    # Clauses tag
    tag = models.CharField('Tag', max_length=300)

    # The avg length of clauses (in words)
    avg_word_count = models.IntegerField(default=0, null=True)


    def set_avgwordcount(self, clauses):
        def word_count(s):
            return len(s.split())

        wcs = map(word_count, clauses)
        avg = sum(wcs) / float(len(wcs))
        self.avg_word_count = int(avg)
        self.save()
        return int(avg)

    def to_dict(self):
        return {
            'tag': self.tag,
            'avg_word_count': self.avg_word_count,
        }

    def __unicode__(self):
        return u'Clauses Statistic [%s]' % (self.tag)
