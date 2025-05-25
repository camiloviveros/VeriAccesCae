# Generated manually to add description and created_by fields

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('access_control', '0005_buildingoccupancy'),
    ]

    operations = [
        migrations.AddField(
            model_name='visitor',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='visitor',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_visitors', to=settings.AUTH_USER_MODEL),
        ),
    ]