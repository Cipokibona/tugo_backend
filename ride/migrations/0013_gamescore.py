from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ride', '0012_ride_share_code'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='GameScore',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mode', models.CharField(choices=[('DRIVER', 'Driver'), ('PEDESTRIAN', 'Pedestrian')], max_length=16)),
                ('score', models.IntegerField(default=0)),
                ('distance', models.PositiveIntegerField(default=0)),
                ('remaining_time', models.PositiveSmallIntegerField(default=0)),
                ('money_delta', models.IntegerField(default=0)),
                ('max_combo', models.PositiveSmallIntegerField(default=0)),
                ('outcome', models.CharField(default='FINISHED', max_length=32)),
                ('payload', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('player', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='game_scores', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-score', '-distance', '-remaining_time', '-created_at'],
            },
        ),
    ]
