from django import template

register = template.Library()

_PERSIAN_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


@register.filter
def persian_intcomma(value):
    """Format an integer with Persian digits and Persian thousands separators."""
    if value is None or value == "":
        return ""

    try:
        formatted = format(int(value), ",")
    except (TypeError, ValueError, OverflowError):
        return value

    return formatted.translate(_PERSIAN_DIGITS).replace(",", "٬")
