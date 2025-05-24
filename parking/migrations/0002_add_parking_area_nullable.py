# parking/migrations/0002_add_parking_area_nullable.py
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('parking', '0001_initial'),
    ]

    operations = [
        # Agregar campo parking_area como nullable primero
        migrations.AddField(
            model_name='vehicle',
            name='parking_area',
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='vehicles',
                to='parking.parkingarea',
                help_text='Área de estacionamiento asignada'
            ),
        ),
        # Agregar campos de timestamp
        migrations.AddField(
            model_name='vehicle',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='vehicle',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
    ]