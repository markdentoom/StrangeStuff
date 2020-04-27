from . import models
from django.contrib import admin


class OrderAdmin(admin.ModelAdmin):
    list_display = ['user', 'ordered']


# Register your models here.
admin.site.register(models.Item)
admin.site.register(models.OrderItem)
admin.site.register(models.Order, OrderAdmin)
admin.site.register(models.Payment)
admin.site.register(models.Coupon)
