from django.urls import reverse
from django.contrib import admin
from django.utils.safestring import mark_safe
from django.http import HttpResponse
import csv, datetime

from .models import Order, OrderItem


# custom action
def export_to_csv(modeladmin, req, queryset):
    opts = modeladmin.model._meta
    content_disposition = f"attachment; filename={opts.verbose_name}.csv"
    resp = HttpResponse(content_type="text/csv")
    resp["Content-Disposition"] = content_disposition
    writer = csv.writer(resp)
    fields = [
        field
        for field in opts.get_fields()
        if not field.many_to_many and not field.one_to_many
    ]

    # write first row with header information
    writer.writerow([field.verbose_name for field in fields])

    # write data rows
    for obj in queryset:
        data_row = []
        for field in fields:
            value = getattr(obj, field.name)

            if isinstance(value, datetime.datetime):
                value = value.strftime("%d/%m/%Y")

            data_row.append(value)
        writer.writerow(data_row)

    return resp


export_to_csv.short_description = "Export to CSV"


def order_payment(obj):
    url = obj.get_stripe_url()
    if obj.stripe_id:
        html = f"<a href='{url}' target='_blank'>{obj.stripe_id}</a>"
        return mark_safe(html)

    return ""


order_payment.short_description = "Stripe payment"


def order_detail(obj):
    url = reverse("orders:admin_order_detail", args=[obj.id])
    return mark_safe(f"<a href='{url}'>View</a>")


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ["product"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "first_name",
        "last_name",
        "email",
        "address",
        "postal_code",
        "city",
        "paid",
        order_payment,
        "created",
        "updated",
        order_detail,
    ]

    list_filter = ["paid", "created", "updated"]
    inlines = [OrderItemInline]
    actions = [export_to_csv]
