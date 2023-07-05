from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import reverse

from .models import Order, OrderItem
from .forms import OrderCreateForm
from cart.cart import Cart
from .tasks import order_created


@staff_member_required
def admin_order_detail(req, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(
        req,
        "admin/orders/order/detail.html",
        {"order": order},
    )


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
