from rest_framework import serializers
from .models import Wallet, WalletTransaction, WithdrawalRequest


class WalletSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user_id', read_only=True)
    class Meta:
        model = Wallet
        fields = ['id', 'user_id', 'balance', 'pending_balance', 'total_earned', 'total_withdrawn', 'created_at']


class TransactionSerializer(serializers.ModelSerializer):
    type = serializers.CharField(source='transaction_type', read_only=True)
    class Meta:
        model = WalletTransaction
        fields = ['id', 'reference', 'type', 'amount', 'status', 'source', 'description', 'created_at']


class WithdrawalSerializer(serializers.ModelSerializer):
    class Meta:
        model = WithdrawalRequest
        fields = ['id', 'amount', 'method', 'phone_number', 'account_holder_name', 'notes', 'status',
                  'requested_at', 'processed_at', 'admin_notes']
        read_only_fields = ['id', 'status', 'requested_at', 'processed_at', 'admin_notes']
