from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('wallet', '0001_initial')]
    operations = [
        migrations.AlterField(model_name='wallet', name='balance', field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=14)),
        migrations.AlterField(model_name='wallet', name='pending_balance', field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=14)),
        migrations.AlterField(model_name='wallet', name='total_earned', field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=14)),
        migrations.AlterField(model_name='wallet', name='total_withdrawn', field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=14)),
    ]
