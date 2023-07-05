from django.shortcuts import render, redirect
from django.urls import reverse
from .models import Order, OrderItem
from .forms import OrderCreateForm
from cart.cart import Cart
from .tasks import order_created


def order_create(req):
    cart = Cart(req)

    if req.method == "POST":
        form = OrderCreateForm(req.POST)
        if form.is_valid():
            order = form.save()

            for item in cart:
                OrderItem.objects.create(
                    order=order,
                    product=item["product"],
                    price=item["price"],
                    quantity=item["quantity"],
                )

            # clear the cart
            cart.clear()

            # launch async task (celery function)
            order_created.delay(order.id)

            # set the order in the session
            req.session["order_id"] = order.id

            # return render(
            #     req,
            #     "orders/order/created.html",
            #     {"order": order},
            # )

            # redirect for payment
            return redirect(reverse("payment:process"))
    else:
        form = OrderCreateForm()

    return render(req, "orders/order/create.html", {"cart": cart, "form": form})
