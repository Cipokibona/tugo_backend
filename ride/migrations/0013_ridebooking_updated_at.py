from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ride', '0012_ride_share_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='ridebooking',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True),
            preserve_default=False,
        ),
    ]
