from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Sum
from store.models import Payment, SalesReport

class Command(BaseCommand):
    help = 'Generate sales reports (today, this month, last month, total) based on completed payments.'

    def handle(self, *args, **options):
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
            obj, created = SalesReport.objects.update_or_create(key=key, defaults={'amount': amt})
            if created:
                self.stdout.write(f'Created report {key}: {amt}')
            else:
                self.stdout.write(f'Updated report {key}: {amt}')

        self.stdout.write(self.style.SUCCESS('Sales reports generation complete.'))
