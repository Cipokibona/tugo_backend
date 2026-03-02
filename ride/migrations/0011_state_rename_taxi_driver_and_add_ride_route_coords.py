# Generated manually to align migration state with current Taxi model.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ride', '0010_rename_taxi_fk_user_remove_servicetaxi_driver'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.RenameField(
                    model_name='taxi',
                    old_name='fk_user',
                    new_name='driver',
                ),
            ],
        ),
        migrations.AddField(
            model_name='ride',
            name='route_coords',
            field=models.JSONField(blank=True, null=True),
        ),
    ]
