# Tugo Money

Tugo Money is an internal BIF wallet and transaction ledger. Wallet methods live in
`wallet.services`; other domains should call these services instead of editing
wallet balances directly. The ride domain calls `wallet.services.credit()` when
its delayed earnings become eligible.

## API

- `GET /api/wallet/` and `GET /api/wallet/transactions/` read the signed-in user's wallet.
- `POST /api/wallet/deposit/` credits a deposit after the existing AfriPay checkout return.
- `POST /api/wallet/withdraw/` reserves available balance and creates a pending request.
- `POST /api/wallet/credit/` is administrator-only; `POST /api/wallet/debit/` and
  `POST /api/wallet/transfer/` operate on the signed-in user's wallet.
- `/api/admin/wallets/*` endpoints require an administrator.

All balance changes and their ledger entries are committed atomically. Outgoing
withdrawals are manual; approving a request does not send funds. Marking it paid
completes the ledger movement.

## Delayed ride earnings

Completed ride earnings are credited after the one-hour dispute window, unless
the ride or booking was cancelled or the booking is disputed. Run the command
once per minute with the deployment scheduler, for example:

```text
python manage.py settle_wallet_rides
```

The settlement is idempotent. Set `RIDE_PLATFORM_COMMISSION_RATE` to configure
the ride application's commission; the wallet package contains no ride policy.

AfriPay currently exposes a checkout redirect but no server-side payment
verification callback in this project. Deposit confirmation follows the same
redirect-based assumption as the existing ride payment flow. Provider callback
verification should replace the redirect confirmation when the provider offers it.
