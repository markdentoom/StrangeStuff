from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('checkout', views.CheckoutView.as_view(), name='checkout'),
    path('product/<slug>', views.ItemDetailView.as_view(), name='product'),
    path('order-summary', views.OrderSummaryView.as_view(), name='order-summary'),
    path('payment/<payment_option>', views.PaymentView.as_view(), name='payment'),

    # This only clears out the cart after a purchase and gives a fake success message
    path('payment/', views.fake_payment_success, name='fake-payment-success'),

    # Cart actions
    path('add-coupon/', views.AddCouponView.as_view(), name='add-coupon'),
    path('add-to-cart/<slug>', views.add_to_cart, name='add-to-cart'),
    path('remove-from-cart/<slug>', views.remove_from_cart, name='remove-from-cart'),
    path('add-single-to-cart/<slug>', views.add_single_to_cart, name='add-single-to-cart'),
    path('remove-single-from-cart/<slug>', views.remove_single_from_cart, name='remove-single-from-cart'),
]
