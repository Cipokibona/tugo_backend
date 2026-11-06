from rest_framework import serializers
from decimal import Decimal
from .models import Wallet, WalletTransaction, WithdrawalRequest


class WalletSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user_id', read_only=True)
    class Meta:
        model = Wallet
        fields = ['id', 'user_id', 'balance', 'pending_balance', 'total_earned', 'total_withdrawn', 'created_at']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        for field in ('balance', 'pending_balance', 'total_earned', 'total_withdrawn'):
            if data[field] is None:
                data[field] = Decimal('0.00')
        return data


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
