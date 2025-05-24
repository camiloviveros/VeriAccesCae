# Generated manually to add approved status

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('access_control', '0003_add_visitor_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='visitor',
            name='status',
            field=models.CharField(choices=[('pending', 'Pendiente'), ('approved', 'Aprobado'), ('inside', 'Dentro'), ('outside', 'Fuera'), ('denied', 'Denegado')], default='pending', max_length=10),
        ),
    ]