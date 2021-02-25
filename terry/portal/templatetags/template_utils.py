from django import template

register = template.Library()


@register.filter
def get_license_name(lic_list):
    return ' or '.join(lic_list)
