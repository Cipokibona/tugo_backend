from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('ride', '0013_gamescore')]
    operations = [
        migrations.AddField(model_name='ride', name='completed_at', field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name='ridebooking', name='payment_method', field=models.CharField(default='AFRIPAY', max_length=16)),
        migrations.AddField(model_name='ridebooking', name='is_disputed', field=models.BooleanField(default=False)),
        migrations.AddField(model_name='ridebooking', name='wallet_settlement', field=models.BooleanField(default=False)),
    ]
