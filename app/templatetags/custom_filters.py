from django import template

register = template.Library()

@register.filter(name='round')
def round_value(value, decimal_places=0):
    try:
        return round(value, decimal_places)
    except (ValueError, TypeError):
        return value
