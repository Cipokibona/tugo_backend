import csv
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.db.models import Sum, Count
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Wallet, WalletTransaction, WithdrawalRequest, Deposit
from .serializers import WalletSerializer, TransactionSerializer, WithdrawalSerializer
from .services import get_wallet, credit, debit, transfer, create_deposit, create_withdrawal, process_withdrawal


class WalletView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        return Response(WalletSerializer(get_wallet(request.user)).data)


class TransactionsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        qs = WalletTransaction.objects.filter(wallet__user=request.user)
        for key, field in [('type', 'transaction_type'), ('status', 'status'), ('source', 'source'), ('reference', 'reference')]:
            if request.query_params.get(key): qs = qs.filter(**{field + '__icontains': request.query_params[key]})
        return Response(TransactionSerializer(qs[:500], many=True).data)


class DepositView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        # Called after the AfriPay redirect, matching the existing ride checkout integration.
        # Provider-side verification can replace this confirmation when AfriPay exposes a callback.
        wallet = create_deposit(request.user, request.data.get('amount'),
                                 request.data.get('payment_method', 'AFRIPAY'), request.data.get('provider_reference', ''))
        return Response(WalletSerializer(wallet).data, status=201)


class WithdrawalView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        qs = WithdrawalRequest.objects.filter(wallet__user=request.user)
        return Response(WithdrawalSerializer(qs, many=True).data)
    def post(self, request):
        serializer = WithdrawalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        obj = create_withdrawal(request.user, **serializer.validated_data)
        return Response(WithdrawalSerializer(obj).data, status=201)


class GenericWalletOperation(APIView):
    permission_classes = [permissions.IsAuthenticated]
    operation = None
    def post(self, request):
        amount = request.data.get('amount')
        user = request.user
        if request.user.is_staff and request.data.get('user_id'):
            user = get_user_model().objects.get(pk=request.data['user_id'])
        if self.operation == 'credit':
            if not request.user.is_staff: return Response({'detail': 'Administrator only.'}, status=403)
            wallet = credit(user, amount, request.data.get('type', 'ADJUSTMENT'), request.data.get('source', 'ADMIN'), request.data.get('description', ''))
        elif self.operation == 'debit':
            wallet = debit(user, amount, request.data.get('type', 'ADJUSTMENT'), request.data.get('source', 'API'), request.data.get('description', ''))
        elif self.operation == 'transfer':
            recipient = get_user_model().objects.get(pk=request.data['recipient_id'])
            transfer(user, recipient, amount, request.data.get('description', ''))
            wallet = get_wallet(user)
        return Response(WalletSerializer(wallet).data)


class CreditView(GenericWalletOperation): operation = 'credit'
class DebitView(GenericWalletOperation): operation = 'debit'
class TransferView(GenericWalletOperation): operation = 'transfer'


class AdminWalletView(APIView):
    permission_classes = [permissions.IsAdminUser]
    def get(self, request):
        qs = Wallet.objects.select_related('user').all()
        query = request.query_params.get('search')
        if query: qs = qs.filter(user__username__icontains=query)
        return Response([dict(WalletSerializer(w).data, user=w.user.username,
                              transaction_count=w.transactions.count()) for w in qs])


class AdminWithdrawalsView(APIView):
    permission_classes = [permissions.IsAdminUser]
    def get(self, request):
        qs = WithdrawalRequest.objects.select_related('wallet__user').all()
        for key, field in [('user', 'wallet__user_id'), ('status', 'status')]:
            if request.query_params.get(key): qs = qs.filter(**{field: request.query_params[key]})
        return Response([dict(WithdrawalSerializer(w).data, user=w.wallet.user.username,
                              user_id=w.wallet.user_id, amount=str(w.amount)) for w in qs])


class AdminDepositsView(APIView):
    permission_classes = [permissions.IsAdminUser]
    def get(self, request):
        return Response([{'id': d.pk, 'user': d.wallet.user.username, 'user_id': d.wallet.user_id,
                          'amount': d.amount, 'method': d.payment_method, 'status': d.status,
                          'reference': d.provider_reference, 'created_at': d.created_at}
                         for d in Deposit.objects.select_related('wallet__user').order_by('-created_at')[:1000]])


class AdminWithdrawalAction(APIView):
    permission_classes = [permissions.IsAdminUser]
    def post(self, request, pk, action):
        obj = WithdrawalRequest.objects.get(pk=pk)
        obj = process_withdrawal(obj, request.user, action, request.data.get('admin_notes', ''))
        return Response(WithdrawalSerializer(obj).data)


class AdminStatsView(APIView):
    permission_classes = [permissions.IsAdminUser]
    def get(self, request):
        today = timezone.localdate()
        tx = WalletTransaction.objects.filter(created_at__date=today)
        return Response({
            'total_money_in_wallets': Wallet.objects.aggregate(v=Sum('balance'))['v'] or Decimal('0'),
            'pending_withdrawals': WithdrawalRequest.objects.filter(status__in=['PENDING','APPROVED']).aggregate(v=Sum('amount'))['v'] or Decimal('0'),
            'completed_withdrawals': WithdrawalRequest.objects.filter(status='COMPLETED').aggregate(v=Sum('amount'))['v'] or Decimal('0'),
            'today_deposits': tx.filter(transaction_type='DEPOSIT').aggregate(v=Sum('amount'))['v'] or Decimal('0'),
            'today_ride_earnings': tx.filter(transaction_type='RIDE_INCOME').aggregate(v=Sum('amount'))['v'] or Decimal('0'),
            'platform_commission': tx.filter(transaction_type='COMMISSION').aggregate(v=Sum('amount'))['v'] or Decimal('0'),
            'wallet_users': Wallet.objects.count(),
        })


class AdminTransactionsView(APIView):
    permission_classes = [permissions.IsAdminUser]
    def get(self, request):
        qs = WalletTransaction.objects.select_related('wallet__user').all()
        filters = {'type': 'transaction_type', 'status': 'status', 'source': 'source', 'reference': 'reference'}
        for key, field in filters.items():
            if request.query_params.get(key): qs = qs.filter(**{field + ('__icontains' if key in ('type','source','reference') else ''): request.query_params[key]})
        if request.query_params.get('user'):
            user_filter = request.query_params['user']
            if user_filter.isdigit(): qs = qs.filter(wallet__user_id=user_filter)
            else: qs = qs.filter(wallet__user__username__icontains=user_filter)
        if request.query_params.get('date'): qs = qs.filter(created_at__date=request.query_params['date'])
        if request.query_params.get('date_from'): qs = qs.filter(created_at__date__gte=request.query_params['date_from'])
        if request.query_params.get('date_to'): qs = qs.filter(created_at__date__lte=request.query_params['date_to'])
        if request.query_params.get('export') == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="tugo-money-transactions.csv"'
            writer = csv.writer(response); writer.writerow(['Reference','User','Type','Amount','Status','Source','Description','Created'])
            for item in qs: writer.writerow([item.reference,item.wallet.user.username,item.transaction_type,item.amount,item.status,item.source,item.description,item.created_at])
            return response
        return Response([dict(TransactionSerializer(t).data, user=t.wallet.user.username, user_id=t.wallet.user_id) for t in qs[:1000]])
