from __future__ import unicode_literals

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from model_utils.models import TimeStampedModel


class Coupon(TimeStampedModel):
    title = models.CharField('Title', max_length=200)
    code = models.CharField('Promo Code', unique=True, max_length=100)
    description = models.TextField('Description', null=True, blank=True)

    max_use_count = models.IntegerField('How many times the coupon can be used',
                                        null=True, blank=True,
                                        validators=[MinValueValidator(1)],
                                        help_text='Leave blank if no such restriction is desired')
    use_count = models.IntegerField('How many times the coupon has been used',
                                    default=0)
    start_date = models.DateTimeField('Coupon available from this date',
                                      null=True, blank=True,
                                      help_text='Optional')
    end_date = models.DateTimeField('Coupon available until this date',
                                    null=True, blank=True,
                                    help_text='Optional')

    @classmethod
    def get_by_code(cls, code):
        return Coupon.objects.filter(code=code.upper()).last()

    @property
    def is_expired(self):
        if self.end_date and timezone.now() > self.end_date:
            return True

        if self.max_use_count and self.use_count >= self.max_use_count:
            return True

        return False

    @property
    def is_available(self):
        if self.start_date and self.start_date > timezone.now():
            return False

        if self.is_expired:
            return False

        return True

    def save(self, *args, **kwargs):
        self.code = self.code.upper()
        super(Coupon, self).save(*args, **kwargs)

    def apply(self):
        if not self.is_available:
            return False

        self.use_count += 1
        self.save()
        return True

    @classmethod
    def apply_by_code(cls, code):
        coupon = cls.get_by_code(code)
        return coupon.apply() if coupon else False

    def __str__(self):
        return self.code
