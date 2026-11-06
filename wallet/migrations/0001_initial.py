import django.db.models.deletion
import wallet.models
from django.conf import settings
from django.db import migrations, models


def create_existing_wallets(apps, schema_editor):
    User = apps.get_model(*settings.AUTH_USER_MODEL.split('.'))
    Wallet = apps.get_model('wallet', 'Wallet')
    Wallet.objects.using(schema_editor.connection.alias).bulk_create(
        [Wallet(user_id=user_id) for user_id in User.objects.using(schema_editor.connection.alias).values_list('pk', flat=True)],
        ignore_conflicts=True,
    )


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name='Wallet', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('balance', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
            ('pending_balance', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
            ('total_earned', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
            ('total_withdrawn', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
            ('created_at', models.DateTimeField(auto_now_add=True)),
            ('updated_at', models.DateTimeField(auto_now=True)),
            ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='wallet', to=settings.AUTH_USER_MODEL)),
        ]),
        migrations.CreateModel(name='WalletTransaction', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('reference', models.CharField(default=wallet.models.transaction_reference, max_length=40, unique=True)),
            ('transaction_type', models.CharField(choices=[('DEPOSIT','Deposit'),('RIDE_PAYMENT','Ride Payment'),('RIDE_INCOME','Ride Income'),('WITHDRAWAL_REQUEST','Withdrawal Request'),('WITHDRAWAL_COMPLETED','Withdrawal Completed'),('WITHDRAWAL_REJECTED','Withdrawal Rejected'),('REFUND','Refund'),('BONUS','Bonus'),('COMMISSION','Commission'),('TRANSFER','Transfer'),('ADJUSTMENT','Adjustment')], max_length=32)),
            ('amount', models.DecimalField(decimal_places=2, max_digits=14)),
            ('status', models.CharField(choices=[('PENDING','Pending'),('COMPLETED','Completed'),('REJECTED','Rejected')], default='COMPLETED', max_length=16)),
            ('source', models.CharField(blank=True, default='API', max_length=80)),
            ('description', models.TextField(blank=True)),
            ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
            ('related_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='related_wallet_transactions', to=settings.AUTH_USER_MODEL)),
            ('wallet', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='transactions', to='wallet.wallet')),
        ], options={'ordering': ['-created_at']}),
        migrations.CreateModel(name='Deposit', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('amount', models.DecimalField(decimal_places=2, max_digits=14)),
            ('payment_method', models.CharField(default='AFRIPAY', max_length=32)),
            ('provider_reference', models.CharField(blank=True, max_length=128, null=True, unique=True)),
            ('status', models.CharField(default='COMPLETED', max_length=16)),
            ('created_at', models.DateTimeField(auto_now_add=True)),
            ('wallet', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='deposits', to='wallet.wallet')),
        ]),
        migrations.CreateModel(name='WithdrawalRequest', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('amount', models.DecimalField(decimal_places=2, max_digits=14)),
            ('method', models.CharField(choices=[('LUMICASH','LUMICASH'),('ECOCASH','ECOCASH'),('ENOTI','ENOTI'),('OTHER','OTHER')], max_length=16)),
            ('phone_number', models.CharField(max_length=32)),
            ('account_holder_name', models.CharField(max_length=160)),
            ('notes', models.TextField(blank=True)),
            ('status', models.CharField(choices=[('PENDING','Pending'),('APPROVED','Approved'),('COMPLETED','Completed'),('REJECTED','Rejected')], db_index=True, default='PENDING', max_length=16)),
            ('requested_at', models.DateTimeField(auto_now_add=True)),
            ('processed_at', models.DateTimeField(blank=True, null=True)),
            ('admin_notes', models.TextField(blank=True)),
            ('processed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='processed_withdrawals', to=settings.AUTH_USER_MODEL)),
            ('wallet', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='withdrawal_requests', to='wallet.wallet')),
        ], options={'ordering': ['-requested_at']}),
        migrations.RunPython(create_existing_wallets, migrations.RunPython.noop),
    ]
