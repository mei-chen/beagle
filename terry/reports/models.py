from __future__ import unicode_literals

import jsonfield
import uuid

from copy import deepcopy

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse

from utils import LICENSES_RISKS


class Report(models.Model):
    url = models.CharField(max_length=300)
    uuid = models.UUIDField(default=uuid.uuid4)
    content = jsonfield.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User)
    public_repo = models.BooleanField(default=True)
    successful = models.BooleanField(default=True)

    def __unicode__(self):
        return "%s %s" % (self.id, self.url)

    def _content_processing(self):
        result = {}
        for k, v in self.content.items():
            if k not in ['licenses', 'stats']:
                result[k] = v
            elif k == 'stats':
                result[k] = deepcopy(v)

        if 'licenses' in self.content:
            result['licenses'] = []
            for i, lib_data in enumerate(self.content['licenses']):
                lics = lib_data[-4]

                # Add license risks to License table
                risks = [-1, None, None, None]

                # Fetch all the licenses in a single query
                for lic_stat in LicenseStatistic.objects.filter(name__in=lics):
                    risk_scores = lic_stat.get_risks()
                    commercial_risk = risk_scores['commercial_score']
                    ip_risk = risk_scores['ip_score']
                    if commercial_risk is None or ip_risk is None:
                        continue
                    combined_risk = int(commercial_risk) + int(ip_risk)
                    if risks[0] < combined_risk:
                        risks[0] = combined_risk
                        risks[1] = commercial_risk
                        risks[2] = ip_risk
                        risks[3] = lic_stat.name

                # Remove orig_lics and treat_as_names, add risks
                # Also place module after library and link
                lib_data = lib_data[:-2]
                lib_data.insert(2, lib_data.pop(0))
                risks = risks[1:]
                result['licenses'].append(lib_data + risks)

            result['licenses_header'] = (
                list(result['licenses_header']) +
                ['Commercial Risk', 'IP Risk', 'Most risky license']
            )

        # Add license risks to Stats table
        if 'stats' in result:
            for i, lic_data in enumerate(result['stats']):
                lic_name = lic_data[0]
                lic_stat = LicenseStatistic.objects.get(name=lic_name)
                risks = lic_stat.get_risks()
                commercial_risk = risks['commercial_score']
                ip_risk = risks['ip_score']
                result['stats'][i] += (commercial_risk, ip_risk)

            result['stats_header'] = (
                list(result['stats_header']) + ['Commercial Risk', 'IP Risk']
            )

            # Calculate total risk score
            risks_count = sum([lic[1] for lic in result['stats']
                               if None not in lic[3:5]])
            risks = []

            for lic in result['stats']:
                # Skip licenses without risk scores
                if None in lic[3:5]:
                    continue
                # Convert 100 (%) into 1.0
                lic_risk = (lic[3] + lic[4]) / 200.0
                risk_weight = lic[1] * 100.0 / risks_count
                risks.append(lic_risk * risk_weight)

            overall_risk_score = int(sum(risks))

            result['overall_risk'] = overall_risk_score

        return result

    @property
    def content_for_frontend(self):
        try:
            return self._content_processing()
        except LicenseStatistic.DoesNotExist:
            # Handle old reports with bugged content
            return {
                'status': 'red',
                'exception': 'Please run Report Reprocess!',
                'git_url': self.content['git_url']
            }


class ReportShared(models.Model):
    report = models.ForeignKey(
        Report,
        related_name='report_shared',
        on_delete=models.CASCADE
    )
    token = models.UUIDField(default=uuid.uuid4)
    user = models.ForeignKey(User)
    created_at = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=100, null=True)

    def share_url(self):
        try:
            return reverse(
                'portal:report_analysis_permalink',
                kwargs={'uuid': unicode(self.token)}
            )

        except Exception:
            # In case it fails don't do anything.
            pass

    def __unicode__(self):
        return "%s" % self.id

    class Meta:
        verbose_name_plural = "Shared Reports"


class LibStatistic(models.Model):
    name = models.CharField(max_length=100)
    version = models.CharField(max_length=20)
    package_manager = models.CharField(max_length=20)
    license = models.CharField(max_length=100)
    licenses = jsonfield.JSONField(default=[])
    copyleft = models.BooleanField(default=False)
    orig_lics = jsonfield.JSONField()
    treat_as = jsonfield.JSONField()
    count = models.PositiveIntegerField()

    def __unicode__(self):
        return "%s/%s" % (self.package_manager, self.name)


class LicenseStatistic(models.Model):
    DEFAULT_RISKS = {
        'commercial_description': None,
        'commercial_score': None,
        'ip_description': None,
        'ip_score': None,
        'source': None
    }

    name = models.CharField(max_length=100, unique=True)
    treat_as = models.CharField(max_length=100)
    count = models.PositiveIntegerField()

    def __unicode__(self):
        return self.name

    def get_risks(self):
        return LICENSES_RISKS.get(self.treat_as, self.DEFAULT_RISKS)


@receiver(post_save, sender=Report)
def save_lib_statistic(sender, instance, **kwargs):
    data = instance.content
    if 'licenses' not in data:
        return
    for (package_manager, name, link, version, licenses, copyleft,
         orig_lics, treat_as_names) in data['licenses']:
        try:
            lib_stat = LibStatistic.objects.get(
                name=name,
                version=version,
                package_manager=package_manager,
                licenses=licenses
            )
            lib_stat.count += 1
            lib_stat.save()
        except LibStatistic.DoesNotExist:
            LibStatistic(
                name=name,
                version=version,
                package_manager=package_manager,
                licenses=licenses,
                count=1,
                copyleft=copyleft,
                orig_lics=orig_lics,
                treat_as=treat_as_names
            ).save()


@receiver(post_save, sender=LibStatistic)
def save_license_statistic(sender, instance, **kwargs):
    for name, treat_as in zip(instance.licenses, instance.treat_as):
        try:
            lic_stat = LicenseStatistic.objects.get(name=name)
            lic_stat.count += 1
            lic_stat.save()
        except LicenseStatistic.DoesNotExist:
            LicenseStatistic(name=name, treat_as=treat_as, count=1).save()
