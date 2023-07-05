import stripe
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from orders.models import Order
from .tasks import payment_completed


@csrf_exempt
def stripe_webhook(req):
    payload = req.body
    sig_header = req.META["HTTP_STRIPE_SIGNATURE"]
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # invalid signature
        return HttpResponse(status=400)

    if event.type == "checkout.session.completed":
        session = event.data.object
        if session.mode == "payment" and session.payment_status == "paid":
            try:
                order = Order.objects.get(id=session.client_reference_id)
            except Order.DoesNotExist:
                return HttpResponse(status=404)

            # mark order as paid
            order.paid = True
            # mark order with stripe payment id
            order.stripe_id = session.payment_intent
            order.save()

            # launch async task of sending email
            payment_completed.delay(order.id)

    return HttpResponse(status=200)
