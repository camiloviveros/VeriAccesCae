
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('security', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='securityincident',
            name='report_type',
            field=models.CharField(
                choices=[
                    ('alert', 'Alerta'),
                    ('emergency', 'Emergencia'),
                    ('incident', 'Incidente'),
                    ('general', 'Reporte General')
                ],
                default='incident',
                max_length=20
            ),
        ),
        migrations.AlterModelOptions(
            name='securityincident',
            options={
                'ordering': ['-created_at'],
                'verbose_name': 'Reporte de Seguridad',
                'verbose_name_plural': 'Reportes de Seguridad'
            },
        ),
    ]