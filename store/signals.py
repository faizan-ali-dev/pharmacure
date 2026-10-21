from django.db.models.signals import post_save, post_delete
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.utils import timezone
from django.db.models import Sum
from .models import Payment, SalesReport, Order
from .cart_utils import transfer_cart_to_user


@receiver(user_logged_in)
def merge_cart_on_login(sender, request, user, **kwargs):
    """Merge anonymous cart with user cart when user logs in"""
    transfer_cart_to_user(request, user)


@receiver(user_logged_out)
def preserve_cart_on_logout(sender, request, user, **kwargs):
    """Cart is already preserved in database, no action needed"""
    pass


def update_sales_reports():
    """Update all sales report entries based on current payment data"""
    now = timezone.now()
    start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_end = start_of_month - timezone.timedelta(seconds=1)
    last_month_start = last_month_end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    completed = Payment.objects.filter(status='Completed')

    total_today = completed.filter(created_at__gte=start_of_today).aggregate(total=Sum('amount'))['total'] or 0
    total_this_month = completed.filter(created_at__gte=start_of_month).aggregate(total=Sum('amount'))['total'] or 0
    total_last_month = completed.filter(created_at__gte=last_month_start, created_at__lte=last_month_end).aggregate(total=Sum('amount'))['total'] or 0
    total_all = completed.aggregate(total=Sum('amount'))['total'] or 0

    reports = {
        'today': total_today,
        'this_month': total_this_month,
        'last_month': total_last_month,
        'total': total_all,
    }

    for key, amt in reports.items():
        SalesReport.objects.update_or_create(key=key, defaults={'amount': amt})


@receiver(post_save, sender=Payment)
def payment_saved(sender, instance, created, **kwargs):
    """Update sales reports when a payment is created or updated"""
    if instance.status == 'Completed':
        update_sales_reports()


@receiver(post_delete, sender=Payment)
def payment_deleted(sender, instance, **kwargs):
    """Update sales reports when a payment is deleted"""
    update_sales_reports()


@receiver(post_save, sender=Order)
def order_status_changed(sender, instance, created, **kwargs):
    """Update sales reports when order status changes to 'Received by User'"""
    if instance.status == 'Received by User':
        # Ensure there's a completed payment for this order
        if hasattr(instance, 'payments') and instance.payments.exists():
            for payment in instance.payments.all():
                if payment.status != 'Completed':
                    payment.status = 'Completed'
                    payment.save()
            update_sales_reports()