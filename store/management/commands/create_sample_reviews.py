from django.core.management.base import BaseCommand
from store.models import Doctor
import random
from datetime import date, timedelta


class Command(BaseCommand):
    help = 'Create sample doctor reviews'

    def handle(self, *args, **options):
        # Reviews feature has been removed from the project.
        self.stdout.write(self.style.WARNING('Reviews feature removed — no action taken.'))
        