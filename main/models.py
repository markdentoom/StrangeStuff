from django.db import models
from django.conf import settings
from django.shortcuts import reverse
from django_countries.fields import CountryField

PRODUCT_CATEGORIES = (
    ('A', 'Attire'),
    ('G', 'Gadget'),
    ('T', 'Toy'),
)

LABEL_CATEGORIES = (
    ('P', 'primary'),
    ('S', 'secondary'),
    ('D', 'danger'),
)


# Create your models here.
class Item(models.Model):
    name = models.CharField(max_length=100)
    price = models.FloatField()
    discount_price = models.FloatField(blank=True, null=True)
    description = models.TextField()
    image = models.ImageField()
    type = models.CharField(choices=PRODUCT_CATEGORIES, max_length=1, default='A')
    label = models.CharField(choices=LABEL_CATEGORIES, max_length=1, default='P')

    slug = models.SlugField()

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('main:product', kwargs={'slug': self.slug})

    def get_add_to_cart_url(self):
        return reverse("main:add-to-cart", kwargs={'slug': self.slug})

    def get_remove_from_cart_url(self):
        return reverse("main:remove-from-cart", kwargs={'slug': self.slug})


class OrderItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    ordered = models.BooleanField(default=False)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return str(self.quantity) + " " + str(self.item.name)

    def get_total_price(self):
        return self.item.price * self.quantity

    def get_total_discount_price(self):
        return self.item.discount_price * self.quantity

    def get_all_total(self):
        if self.item.discount_price:
            return self.get_total_discount_price()
        return self.get_total_price()


class Order(models.Model):  # Order models separate from OrderItem to allow for a persistent shopping cart
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    ordered = models.BooleanField(default=False)
    items = models.ManyToManyField(OrderItem)
    start_date = models.DateTimeField(auto_now_add=True)
    ordered_date = models.DateTimeField(default=False)
    # add info from BillingAddress
    billing_address = models.ForeignKey('BillingAddress', on_delete=models.SET_NULL, blank=True, null=True)
    # refers to Payment class down below
    payment = models.ForeignKey('Payment', on_delete=models.SET_NULL, blank=True, null=True)
    # links to coupon
    coupon = models.ForeignKey('Coupon', on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return self.user.username

    def get_total(self):
        total = 0
        for order_item in self.items.all():
            total += order_item.get_all_total()
        if self.coupon:
            total -= self.coupon.amount
        return total


class BillingAddress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    address = models.CharField(max_length=100)
    address2 = models.CharField(max_length=100)
    country = CountryField(multiple=False)
    zip = models.CharField(max_length=100)

    def __str__(self):
        return self.user.username


class Payment(models.Model):
    strip_charge_id = models.CharField(max_length=50)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True)
    amount = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username


class Coupon(models.Model):
    code = models.CharField(max_length=15)
    amount = models.FloatField()

    def __str__(self):
        return self.code
