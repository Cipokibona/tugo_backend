"""Atomic wallet operations shared by all Tugo applications."""
from decimal import Decimal
from django.db import transaction
from django.db.models import F
from rest_framework.exceptions import ValidationError
from .models import Wallet, WalletTransaction, WithdrawalRequest, Deposit


def get_wallet(user):
    wallet, _ = Wallet.objects.get_or_create(user=user)
    return wallet


@transaction.atomic
def credit(user, amount, transaction_type='BONUS', source='API', description='', related_user=None):
    amount = Decimal(str(amount))
    if amount <= 0:
        raise ValidationError({'amount': 'Amount must be greater than zero.'})
    wallet = Wallet.objects.select_for_update().get(pk=get_wallet(user).pk)
    wallet.balance = F('balance') + amount
    if transaction_type in ('RIDE_INCOME', 'BONUS'):
        wallet.total_earned = F('total_earned') + amount
    wallet.save(update_fields=['balance', 'total_earned', 'updated_at'])
    wallet.refresh_from_db()
    WalletTransaction.objects.create(wallet=wallet, transaction_type=transaction_type, amount=amount,
        source=source, description=description, related_user=related_user)
    return wallet


@transaction.atomic
def debit(user, amount, transaction_type='ADJUSTMENT', source='API', description='', related_user=None):
    amount = Decimal(str(amount))
    if amount <= 0:
        raise ValidationError({'amount': 'Amount must be greater than zero.'})
    wallet = Wallet.objects.select_for_update().get(pk=get_wallet(user).pk)
    if wallet.balance < amount:
        raise ValidationError({'amount': 'Insufficient wallet balance.'})
    wallet.balance = F('balance') - amount
    wallet.save(update_fields=['balance', 'updated_at'])
    wallet.refresh_from_db()
    WalletTransaction.objects.create(wallet=wallet, transaction_type=transaction_type, amount=-amount,
        source=source, description=description, related_user=related_user)
    return wallet


@transaction.atomic
def transfer(sender, recipient, amount, description=''):
    debit(sender, amount, 'TRANSFER', 'WALLET', description, recipient)
    credit(recipient, amount, 'TRANSFER', 'WALLET', description, sender)


@transaction.atomic
def create_deposit(user, amount, payment_method='AFRIPAY', provider_reference=''):
    if provider_reference:
        existing = Deposit.objects.filter(provider_reference=provider_reference).select_related('wallet').first()
        if existing:
            if existing.wallet.user_id != getattr(user, 'pk', user):
                raise ValidationError({'provider_reference': 'This reference belongs to another wallet.'})
            return existing.wallet
    wallet = credit(user, amount, 'DEPOSIT', payment_method, 'Wallet deposit')
    Deposit.objects.create(wallet=wallet, amount=Decimal(str(amount)), payment_method=payment_method,
                           provider_reference=provider_reference or None)
    return wallet


@transaction.atomic
def create_withdrawal(user, amount, method, phone_number, account_holder_name, notes=''):
    amount = Decimal(str(amount))
    if amount <= 0:
        raise ValidationError({'amount': 'Amount must be greater than zero.'})
    wallet = Wallet.objects.select_for_update().get(pk=get_wallet(user).pk)
    if wallet.balance < amount:
        raise ValidationError({'amount': 'Insufficient available balance.'})
    wallet.balance = F('balance') - amount
    wallet.pending_balance = F('pending_balance') + amount
    wallet.save(update_fields=['balance', 'pending_balance', 'updated_at'])
    wallet.refresh_from_db()
    request = WithdrawalRequest.objects.create(wallet=wallet, amount=amount, method=method,
        phone_number=phone_number, account_holder_name=account_holder_name, notes=notes)
    WalletTransaction.objects.create(wallet=wallet, transaction_type='WITHDRAWAL_REQUEST', amount=-amount,
        status='PENDING', source='WITHDRAWAL', description=f'Withdrawal request {request.pk}')
    return request


@transaction.atomic
def process_withdrawal(request_obj, actor, decision, admin_notes=''):
    request_obj = WithdrawalRequest.objects.select_for_update().select_related('wallet').get(pk=request_obj.pk)
    if request_obj.status not in ('PENDING', 'APPROVED'):
        raise ValidationError({'status': 'This withdrawal is already processed.'})
    wallet = Wallet.objects.select_for_update().get(pk=request_obj.wallet_id)
    if decision == 'approve':
        request_obj.status = 'APPROVED'
    elif decision in ('reject', 'paid'):
        wallet.pending_balance = F('pending_balance') - request_obj.amount
        fields = ['pending_balance', 'updated_at']
        if decision == 'reject':
            wallet.balance = F('balance') + request_obj.amount
            fields.append('balance')
            tx_type, tx_amount, tx_status = 'WITHDRAWAL_REJECTED', request_obj.amount, 'REJECTED'
            request_obj.status = 'REJECTED'
        else:
            wallet.total_withdrawn = F('total_withdrawn') + request_obj.amount
            fields.append('total_withdrawn')
            tx_type, tx_amount, tx_status = 'WITHDRAWAL_COMPLETED', -request_obj.amount, 'COMPLETED'
            request_obj.status = 'COMPLETED'
        wallet.save(update_fields=fields)
        WalletTransaction.objects.create(wallet=wallet, transaction_type=tx_type, amount=tx_amount,
            status=tx_status, source='WITHDRAWAL', description=f'Withdrawal request {request_obj.pk}')
    else:
        raise ValidationError({'decision': 'Unknown action.'})
    request_obj.processed_by = actor
    request_obj.processed_at = timezone.now() if decision != 'approve' else None
    request_obj.admin_notes = admin_notes
    request_obj.save()
    return request_obj
