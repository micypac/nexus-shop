from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from shop.models import Product
from .cart import Cart
from .forms import CartAddProductForm
from coupons.forms import CouponApplyForm
from shop.recommender import Recommender


@require_POST
def cart_add(req, product_id):
    cart = Cart(req)
    product = get_object_or_404(Product, id=product_id)
    form = CartAddProductForm(req.POST)

    if form.is_valid():
        cd = form.cleaned_data
        cart.add(
            product=product, quantity=cd["quantity"], override_quantity=cd["override"]
        )

    return redirect("cart:cart_detail")


@require_POST
def cart_remove(req, product_id):
    cart = Cart(req)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    return redirect("cart:cart_detail")


def cart_detail(req):
    cart = Cart(req)

    for item in cart:
        item["update_quantity_form"] = CartAddProductForm(
            initial={"quantity": item["quantity"], "override": True}
        )

    # display coupon form
    coupon_apply_form = CouponApplyForm()

    # get items recommendations
    r = Recommender()
    cart_prods = [item["product"] for item in cart]
    if cart_prods:
        recommended_prods = r.suggest_products_for(cart_prods, max_results=4)
    else:
        recommended_prods = []

    return render(
        req,
        "cart/detail.html",
        {
            "cart": cart,
            "coupon_apply_form": coupon_apply_form,
            "recommended_prods": recommended_prods,
        },
    )
