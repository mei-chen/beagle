import traceback

from django.core.management.base import BaseCommand
from reports.models import LibStatistic, Report
from snoopy.utils import (
    lic_separator_re, simplify_lic_name, treat_as_rules, rewrite_rules
)


class Command(BaseCommand):
    help = 'Re-saves all lib statistics objects while calculating missing' \
           'data to create corresponding license statistics.' \
           '. usage: ./manage.py create_license_statistics'

    def handle(self, *args, **options):
        self.stdout.write('Starting...')
        try:
            for lib_stat in LibStatistic.objects.all():
                if lib_stat.licenses:
                    continue
                names = lic_separator_re.split(lib_stat.license)
                treat_as_names = []
                rewritten_names = []
                for name in names:
                    simplified = simplify_lic_name(name)
                    if simplified in rewrite_rules:
                        name = rewrite_rules[simplified]
                    if simplified in treat_as_rules:
                        treat_as = treat_as_rules[simplified]
                    else:
                        treat_as = name

                    rewritten_names.append(name)
                    treat_as_names.append(treat_as)

                lib_stat.treat_as = treat_as_names
                lib_stat.licenses = rewritten_names
                lib_stat.save()

            # This process can create duplicate LibStatistics
            # So we get rid of duplicates
            for lib_stat in LibStatistic.objects.all():
                lib_stats = LibStatistic.objects.filter(
                    name=lib_stat.name,
                    version=lib_stat.version,
                    package_manager=lib_stat.package_manager,
                    licenses=lib_stat.licenses
                )
                for lib_stat in lib_stats[1:]:
                    lib_stat.delete()

        except Exception as e:
            self.stderr.write('Encountered error: %s' % str(e))
            self.stderr.write(traceback.format_exc())

        self.stdout.write('Finished!')
