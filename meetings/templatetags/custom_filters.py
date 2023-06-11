from django import template

register = template.Library()

@register.filter
def range_months(current_month):
    return range(1, current_month+1)
