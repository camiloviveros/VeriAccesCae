
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('parking', '0003_populate_parking_areas'),
    ]

    operations = [
        # Hacer el campo parking_area obligatorio
        migrations.AlterField(
            model_name='vehicle',
            name='parking_area',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='vehicles',
                to='parking.parkingarea',
                help_text='Área de estacionamiento asignada'
            ),
        ),
    ]