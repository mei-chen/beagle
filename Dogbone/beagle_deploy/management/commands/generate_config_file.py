from optparse import make_option

from django.conf import settings
from django.template import Context, Template
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Generate a proper config file given a settings file and a template'

    option_list = BaseCommand.option_list + (
        make_option('--template', help='The path to the template'),
        make_option('--output', help='where to save the file'),
    )

    def handle(self, *args, **options):
        if 'template' not in options or not options['template']:
            raise CommandError('Please specify a template. Use --template option')

        if 'output' not in options or not options['output']:
            raise CommandError('Please specify an output file. Use --output option')

        settings_dict = {}

        for attr_name in dir(settings):
            attr = getattr(settings, attr_name)
            if hasattr(attr, '__call__') or attr_name.startswith('__'):
                continue

            settings_dict[attr_name] = attr

        template = Template(open(options['template'], 'r').read())
        context = Context(settings_dict)

        with open(options['output'], 'w+') as output:
            output.write(template.render(context))

