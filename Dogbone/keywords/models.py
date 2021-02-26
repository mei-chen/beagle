from nltk import word_tokenize
from model_utils.models import TimeStampedModel

from django.db import models
from django.contrib.auth.models import User

from .signals import keyword_activated, keyword_created, keyword_deactivated, keyword_deleted


class ActiveManager(models.Manager):
    """
    Get all objects that are active
    """
    def get_query_set(self):
        return super(ActiveManager, self).get_query_set().filter(active=True)


class InactiveManager(models.Manager):
    """
    Get all objects that aren't active
    """
    def get_query_set(self):
        return super(InactiveManager, self).get_query_set().filter(active=False)


class ActiveModel(models.Model):
    """
    Abstract Django model for modeling objects that can be in an active/inactive state
    """
    active = models.BooleanField(default=True)

    # Model managers
    objects = models.Manager()
    activated = ActiveManager()
    deactivated = InactiveManager()

    def activate(self):
        """
        Make the model active
        """
        self.active = True
        self.save()

    def deactivate(self):
        """
        Make the model inactive
        """
        self.active = False
        self.save()

    class Meta:
        abstract = True


class SearchKeyword(TimeStampedModel, ActiveModel):
    """
    User associated keyword Django model
    """
    keyword = models.CharField(max_length=200)
    exact_match = models.BooleanField(default=False)
    owner = models.ForeignKey(User, related_name='keywords')

    @staticmethod
    def make_standard(keyword):
        """
        Transform the keyword to a standard format
        :param keyword: the keyword string
        :return: the standardized keyword string
        """
        return keyword.lower().strip()

    @staticmethod
    def add(user, keyword):
        """
        Add a keyword for a user
        :param user: the keyword owner
        :param keyword: the keyword string
        :return: the `SearchKeyword` Django model
        """
        return SearchKeyword.objects.create(owner=user,
                                            keyword=keyword)

    def matches(self, text):
        """
        Check if the keyword is found in the text
        :param text: a string
        :return: True/False
        """
        standard_text = self.make_standard(text)
        if self.exact_match:
            return self.keyword in word_tokenize(standard_text)
        return self.keyword in standard_text

    def save(self, *args, **kwargs):
        """
        - Standardize the keyword before saving
        - Emit the `keyword_created` signal
        """
        self.keyword = SearchKeyword.make_standard(self.keyword)

        send_created_signal = False
        if not self.pk:
            send_created_signal = True

        result = super(SearchKeyword, self).save(*args, **kwargs)

        if send_created_signal:
            keyword_created.send(self.__class__, user=self.owner, keyword=self)

        return result

    def delete(self, using=None):
        """
        - Emit the `keyword_deleted` signal
        :param using:
        :return:
        """
        keyword_deleted.send(self.__class__, user=self.owner, keyword=self)
        return super(SearchKeyword, self).delete(using=using)

    def activate(self):
        """
        - Emit the `keyword_activated` signal
        :return:
        """
        super(SearchKeyword, self).activate()
        keyword_activated.send(self.__class__, user=self.owner, keyword=self)

    def deactivate(self):
        """
        - Emit the `keyword_deactivated` signal
        :return:
        """
        super(SearchKeyword, self).deactivate()
        keyword_deactivated.send(self.__class__, user=self.owner, keyword=self)

    def to_dict(self):
        """
        Serialize a `SearchKeyword` model
        :return: a dict
        """
        return {
            'keyword': self.keyword,
            'active': self.active,
            'created': str(self.created),
            'exact_match': self.exact_match
        }

    def __unicode__(self):
        return "%s%s - <%s>" % ('' if self.active else '[!] ', self.owner, self.keyword)

    class Meta:
        # Display Meta Options
        verbose_name = 'Search Keyword'
        verbose_name_plural = 'Search Keywords'

        # Ordering Options
        ordering = ['keyword', 'owner', ]

        unique_together = (("owner", "keyword"),)
