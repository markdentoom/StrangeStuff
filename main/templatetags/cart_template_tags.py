from django import template
from main.models import Order

register = template.Library()


@register.filter
def cart_item_counter(user):
    if user.is_authenticated:
        query = Order.objects.filter(user=user, ordered=False)  # don't query previously ordered items
        if query:
            return query[0].items.count()
    return 0
