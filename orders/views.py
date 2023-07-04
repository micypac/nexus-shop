from django.shortcuts import render
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

            # launch async task
            order_created.delay(order.id)

            return render(
                req,
                "orders/order/created.html",
                {"order": order},
            )
    else:
        form = OrderCreateForm()

    return render(req, "orders/order/create.html", {"cart": cart, "form": form})
