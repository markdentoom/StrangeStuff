from django.shortcuts import render, get_object_or_404
from django.views.generic import View, ListView, DetailView
from django.contrib import messages
from django.utils import timezone
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required  # use decorators for function based views
from django.contrib.auth.mixins import LoginRequiredMixin  # use mixins for class based views
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from . import models, forms


import stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


# Create your views here.
def products(request):
    context = {
        'items': models.Item.objects.all()
    }
    return render(request, 'products.html', context=context)


# Button on product page
@login_required
def add_to_cart(request, slug):
    item = get_object_or_404(models.Item, slug=slug)
    order_item, created = models.OrderItem.objects.get_or_create(item=item, user=request.user, ordered=False)
    order_request = models.Order.objects.filter(user=request.user, ordered=False)
    # check if order exists
    if order_request:
        order = order_request[0]
        if order.items.filter(item__slug=item.slug):
            messages.info(request, "Item already in cart.")
        else:
            order.items.add(order_item)
            messages.info(request, "Item added to cart.")
    else:
        ordered_date = timezone.now()
        order = models.Order.objects.create(user=request.user, ordered_date=ordered_date)
        order.items.add(order_item)
        messages.info(request, "Item added to cart.")
    return redirect("main:product", slug=slug)


# DEPRECATED: Button on product page
@login_required
def remove_from_cart(request, slug):
    # refer to add_to_cart for most of the code
    item = get_object_or_404(models.Item, slug=slug)
    order_request = models.Order.objects.filter(user=request.user, ordered=False)
    if order_request:
        order = order_request[0]
        if order.items.filter(item__slug=item.slug):
            order_item = models.OrderItem.objects.filter(item=item, user=request.user, ordered=False)[0]
            order.items.remove(order_item)
            messages.info(request, "Item removed from cart.")
            return redirect('main:order-summary')
        else:
            messages.info(request, "Item not in cart.")
            return redirect('main:product', slug=slug)
    else:
        messages.info(request, "You have no order for this item.")
        return redirect('main:product', slug=slug)


# Button on order-summary page
@login_required
def remove_single_from_cart(request, slug):
    # refer to add_to_cart for most of the code
    item = get_object_or_404(models.Item, slug=slug)
    order_request = models.Order.objects.filter(user=request.user, ordered=False)
    if order_request:
        order = order_request[0]
        if order.items.filter(item__slug=item.slug):
            order_item = models.OrderItem.objects.filter(item=item, user=request.user, ordered=False)[0]
            if order_item.quantity == 1:
                order.items.remove(order_item)
                messages.info(request, "Item removed from cart.")
            else:
                order_item.quantity -= 1
                order_item.save()
        else:
            # This should never happen
            messages.info(request, "Item not in cart.")
    else:
        # This should never happen
        messages.info(request, "You have no order for this item.")
    return redirect('main:order-summary')


# Button on order-summary page
@login_required
def add_single_to_cart(request, slug):
    item = get_object_or_404(models.Item, slug=slug)
    order_item, created = models.OrderItem.objects.get_or_create(item=item, user=request.user, ordered=False)
    order_request = models.Order.objects.filter(user=request.user, ordered=False)
    # check if order exists
    if order_request:
        order = order_request[0]
        if order.items.filter(item__slug=item.slug):
            order_item.quantity += 1
            order_item.save()
        else:
            # This should never happen
            order.items.add(order_item)
            messages.info(request, "Item added to cart.")
    else:
        # This should never happen
        ordered_date = timezone.now()
        order = models.Order.objects.create(user=request.user, ordered_date=ordered_date)
        order.items.add(order_item)
        messages.info(request, "Item added to cart.")
    return redirect('main:order-summary')


class HomeView(ListView):
    model = models.Item
    paginate_by = 8
    template_name = 'home.html'


class ItemDetailView(DetailView):
    model = models.Item
    template_name = 'product.html'


class OrderSummaryView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            order = models.Order.objects.get(user=self.request.user, ordered=False)
            context = {'object': order}
            return render(self.request, 'order-summary.html', context=context)
        except ObjectDoesNotExist:
            messages.warning(self.request, 'There are no items in the cart')
            return redirect('/')


class CheckoutView(View):
    def get(self, *args, **kwargs):
        try:
            order = models.Order.objects.get(user=self.request.user, ordered=False)
            form = forms.CheckoutForm()
            context = {'form': form, 'couponform': forms.CouponForm(), 'order': order, 'DISPLAY_COUPON_FORM': True}
            return render(self.request, 'checkout.html', context=context)
        except ObjectDoesNotExist:
            messages.info(self.request, 'You have no active order')
            return redirect('main:checkout')

    def post(self, *args, **kwargs):
        form = forms.CheckoutForm(self.request.POST or None)
        try:  # if the order exists, check if it's valid and then save it if it is.
            order = models.Order.objects.get(user=self.request.user, ordered=False)
            if form.is_valid():
                # info from the CheckoutForm from forms.py
                address = form.cleaned_data.get('address')
                address2 = form.cleaned_data.get('address2')
                country = form.cleaned_data.get('country')
                zip = form.cleaned_data.get('zip')
                # todo split shipping and billing address
                # same_shipping_address = form.cleaned_data.get('same_shipping_address')
                # save_info = form.cleaned_data.get('save_info')
                payment_option = form.cleaned_data.get('payment_option')
                billing_address = models.BillingAddress(
                    # info from the BillingAddress from model.py
                    user=self.request.user,
                    address=address,
                    address2=address2,
                    country=country,
                    zip=zip,
                )
                billing_address.save()
                order.billing_address = billing_address
                order.save()
                # todo redirect to the right payment option
                if payment_option == 'S':
                    return redirect('main:payment', payment_option='Stripe')
                elif payment_option == 'P':
                    return redirect('main:payment', payment_option='PayPal')
                else:
                    messages.warning(self.request, 'Invalid payment option selected')
                    return redirect('main:checkout')
            messages.warning(self.request, 'Failed checkout')
            return redirect('main:checkout')
        except ObjectDoesNotExist:
            messages.warning(self.request, 'You have no active order')
            return redirect('main:order-summary')


# The actual payment view.
class PaymentView(View):
    def get(self, *args, **kwargs):
        order = models.Order.objects.get(user=self.request.user, ordered=False)
        if order.billing_address:
            context = {'order': order, 'DISPLAY_COUPON_FORM': False}
            return render(self.request, 'payment.html', context=context)
        else:
            messages.warning(self.request, 'Please add a billing address')
            return redirect('main:checkout')

    def post(self, *args, **kwargs):
        order = models.Order.objects.get(user=self.request.user, ordered=False)
        # `source` is obtained with Stripe.js; see https://stripe.com/docs/payments/accept-a-payment-charges#web-create-token
        token = self.request.POST.get('stripeToken')
        amount = int(order.get_total() * 100)

        # stripe error handling: https://stripe.com/docs/api/expanding_objects?lang=python
        try:
            charge = stripe.Charge.create(
                amount=amount,
                currency="eur",
                source=token,
            )

            # create payment
            payment = models.Payment()
            payment.stripe_charge_id = charge['id']
            payment.user = self.request.user
            payment.amount = order.get_total()
            payment.save()

            # Make sure old and new orders don't overlap
            order_items = order.items.all()
            order_items.update(ordered=True)
            for item in order_items:
                item.save()

            # link payment to order
            order.ordered = True
            order.payment = payment
            order.save()

            messages.success(self.request, 'Your order was successful!')
            return redirect('/')

        # failed payment handling
        except stripe.error.CardError as e:
            # Since it's a decline, stripe.error.CardError will be caught
            messages.warning(self.request, f'Message is: {e.error.message}')
            return redirect('/')
        except stripe.error.RateLimitError as e:
            # Too many requests made to the API too quickly
            messages.warning(self.request, f'RateLimitError')
            return redirect('/')
        except stripe.error.InvalidRequestError as e:
            # Invalid parameters were supplied to Stripe's API
            messages.warning(self.request, f'InvalidRequestError')
            return redirect('/')
        except stripe.error.AuthenticationError as e:
            # Authentication with Stripe's API failed
            # (maybe you changed API keys recently)
            messages.warning(self.request, f'AuthenticationError')
            return redirect('/')
        except stripe.error.APIConnectionError as e:
            # Network communication with Stripe failed
            messages.warning(self.request, f'APIConnectionError')
            return redirect('/')
        except stripe.error.StripeError as e:
            # Display a very generic error to the user, and maybe send
            # yourself an email
            messages.warning(self.request, f'Something went wrong. Please try again.')
            return redirect('/')
        except Exception as e:
            # Something else happened, completely unrelated to Stripe; send email to self
            messages.warning(self.request, f'A developer messed something up. An error report has been sent to their email.')
            return redirect('/')


# This only clears out the cart after a purchase and gives a fake success message
def fake_payment_success(request):
    order = models.Order.objects.get(user=request.user, ordered=False)
    payment = models.Payment()
    payment.user = request.user
    payment.amount = order.get_total()
    payment.save()

    # Make sure old and new orders don't overlap
    order_items = order.items.all()
    order_items.update(ordered=True)
    for item in order_items:
        item.save()

    # link payment to order
    order.ordered = True
    order.payment = payment
    order.save()

    messages.success(request, 'Your order was successful! (no money has been deducted from the account)')
    return redirect('/')


def get_coupon(request, code):
    try:
        coupon = models.Coupon.objects.get(code=code)
        return coupon
    # fixme ValueError when entering wrong coupon
    except ObjectDoesNotExist:
        messages.info(request, 'Invalid coupon')
        return redirect("main:checkout")


class AddCouponView(View):
    def post(self, *args, **kwargs):
        form = forms.CouponForm(self.request.POST or None)
        if form.is_valid():
            try:
                code = form.cleaned_data.get('code')
                order = models.Order.objects.get(user=self.request.user, ordered=False)
                order.coupon = get_coupon(self.request, code)
                order.save()
                messages.success(self.request, 'Added coupon')
                return redirect('main:checkout')
            except ObjectDoesNotExist:
                messages.info(self.request, 'You have no active order')
                return redirect('main:checkout')
