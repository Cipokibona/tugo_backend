from django.urls import path
from .views import (WalletView, TransactionsView, DepositView, WithdrawalView, CreditView, DebitView,
                    TransferView, AdminWalletView, AdminWithdrawalsView, AdminWithdrawalAction,
                    AdminStatsView, AdminTransactionsView, AdminDepositsView)

urlpatterns = [
    path('wallet/', WalletView.as_view()),
    path('wallet/transactions/', TransactionsView.as_view()),
    path('wallet/deposit/', DepositView.as_view()),
    path('wallet/withdraw/', WithdrawalView.as_view()),
    path('wallet/credit/', CreditView.as_view()),
    path('wallet/debit/', DebitView.as_view()),
    path('wallet/transfer/', TransferView.as_view()),
    path('admin/wallets/', AdminWalletView.as_view()),
    path('admin/wallets/stats/', AdminStatsView.as_view()),
    path('admin/wallets/transactions/', AdminTransactionsView.as_view()),
    path('admin/wallets/withdrawals/', AdminWithdrawalsView.as_view()),
    path('admin/wallets/deposits/', AdminDepositsView.as_view()),
    path('admin/wallets/withdrawals/<int:pk>/<str:action>/', AdminWithdrawalAction.as_view()),
]
