import uuid
from decimal import Decimal
from django.conf import settings
from django.db import models


def transaction_reference():
    return uuid.uuid4().hex.upper()


class Wallet(models.Model):
    """Internal ledger balance. Every balance change is backed by a transaction."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    pending_balance = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    total_earned = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    total_withdrawn = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Wallet: {self.user}'


class WalletTransaction(models.Model):
    TYPES = [(v, v.replace('_', ' ').title()) for v in (
        'DEPOSIT', 'RIDE_PAYMENT', 'RIDE_INCOME', 'WITHDRAWAL_REQUEST',
        'WITHDRAWAL_COMPLETED', 'WITHDRAWAL_REJECTED', 'REFUND', 'BONUS',
        'COMMISSION', 'TRANSFER', 'ADJUSTMENT')]
    STATUSES = [('PENDING', 'Pending'), ('COMPLETED', 'Completed'), ('REJECTED', 'Rejected')]
    wallet = models.ForeignKey(Wallet, on_delete=models.PROTECT, related_name='transactions')
    reference = models.CharField(max_length=40, unique=True, default=transaction_reference)
    transaction_type = models.CharField(max_length=32, choices=TYPES)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    status = models.CharField(max_length=16, choices=STATUSES, default='COMPLETED')
    source = models.CharField(max_length=80, blank=True, default='API')
    description = models.TextField(blank=True)
    related_user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='related_wallet_transactions')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']


class WithdrawalRequest(models.Model):
    METHODS = [(v, v) for v in ('LUMICASH', 'ECOCASH', 'ENOTI', 'OTHER')]
    STATUSES = [(v, v.title()) for v in ('PENDING', 'APPROVED', 'COMPLETED', 'REJECTED')]
    wallet = models.ForeignKey(Wallet, on_delete=models.PROTECT, related_name='withdrawal_requests')
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    method = models.CharField(max_length=16, choices=METHODS)
    phone_number = models.CharField(max_length=32)
    account_holder_name = models.CharField(max_length=160)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=16, choices=STATUSES, default='PENDING', db_index=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    processed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='processed_withdrawals')
    admin_notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-requested_at']


class Deposit(models.Model):
    wallet = models.ForeignKey(Wallet, on_delete=models.PROTECT, related_name='deposits')
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    payment_method = models.CharField(max_length=32, default='AFRIPAY')
    provider_reference = models.CharField(max_length=128, blank=True, null=True, unique=True)
    status = models.CharField(max_length=16, default='COMPLETED')
    created_at = models.DateTimeField(auto_now_add=True)
