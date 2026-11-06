from django.contrib import admin
from .models import Wallet, WalletTransaction, WithdrawalRequest, Deposit


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'pending_balance', 'total_earned', 'total_withdrawn')
    search_fields = ('user__username', 'user__email')


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ('reference', 'wallet', 'transaction_type', 'amount', 'status', 'source', 'created_at')
    list_filter = ('transaction_type', 'status', 'source', 'created_at')
    search_fields = ('reference', 'wallet__user__username', 'description')


@admin.register(WithdrawalRequest)
class WithdrawalRequestAdmin(admin.ModelAdmin):
    list_display = ('wallet', 'amount', 'method', 'phone_number', 'status', 'requested_at', 'processed_at')
    list_filter = ('status', 'method', 'requested_at')
    search_fields = ('wallet__user__username', 'phone_number', 'account_holder_name')


@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    list_display = ('wallet', 'amount', 'payment_method', 'status', 'provider_reference', 'created_at')
    list_filter = ('status', 'payment_method', 'created_at')
