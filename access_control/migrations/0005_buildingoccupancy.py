# Generated manually for BuildingOccupancy

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('access_control', '0004_add_approved_status'),
    ]

    operations = [
        migrations.CreateModel(
            name='BuildingOccupancy',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('residents_count', models.IntegerField(default=0)),
                ('visitors_count', models.IntegerField(default=0)),
                ('max_capacity', models.IntegerField(default=100)),
                ('last_updated', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Building Occupancy',
                'verbose_name_plural': 'Building Occupancy',
            },
        ),
    ]