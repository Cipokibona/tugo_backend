from django.core.management.base import BaseCommand
from ride.services import settle_completed_ride_earnings


class Command(BaseCommand):
    help = 'Credit eligible ride earnings that have been completed for at least one hour.'

    def handle(self, *args, **options):
        count = settle_completed_ride_earnings()
        self.stdout.write(self.style.SUCCESS(f'Settled {count} ride booking(s).'))
