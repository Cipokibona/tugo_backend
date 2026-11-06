"""Ride domain workflows that consume the generic Tugo Money wallet service."""
from datetime import timedelta
from decimal import Decimal
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from wallet.models import WalletTransaction
from wallet.services import credit
from .models import Ride, RideBooking


@transaction.atomic
def settle_completed_ride_earnings():
    """Credit eligible driver earnings once a completed ride has passed its dispute window."""
    cutoff = timezone.now() - timedelta(hours=1)
    commission_rate = Decimal(str(getattr(settings, 'RIDE_PLATFORM_COMMISSION_RATE', '0.10')))
    rides = Ride.objects.filter(status='COMPLETED', completed_at__lte=cutoff).select_related('driver')
    settled = 0
    for ride in rides:
        if not ride.driver:
            continue
        bookings = RideBooking.objects.filter(ride=ride, status='CONFIRMED', is_disputed=False,
                                               wallet_settlement=False).select_related('passenger')
        for booking in bookings:
            net = (Decimal(str(ride.price)) * (Decimal('1') - commission_rate)).quantize(Decimal('0.01'))
            credit(ride.driver, net, 'RIDE_INCOME', 'RIDE', f'Net earnings for ride {ride.pk}', booking.passenger)
            WalletTransaction.objects.create(wallet=ride.driver.wallet, transaction_type='COMMISSION',
                amount=(Decimal(str(ride.price)) * commission_rate).quantize(Decimal('0.01')),
                source='RIDE', description=f'Platform commission retained for ride {ride.pk} (informational)')
            booking.wallet_settlement = True
            booking.save(update_fields=['wallet_settlement'])
            settled += 1
    return settled
