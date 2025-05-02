# Generated manually to fix missing status field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('access_control', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='visitor',
            name='status',
            field=models.CharField(choices=[('pending', 'Pendiente'), ('inside', 'Dentro'), ('outside', 'Fuera'), ('denied', 'Denegado')], default='pending', max_length=10),
        ),
        migrations.AddField(
            model_name='visitor',
            name='visitor_type',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='visitor',
            name='apartment_number',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='visitor',
            name='entry_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='visitor',
            name='exit_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]