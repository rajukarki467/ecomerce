# Generated by Django 5.0.4 on 2024-06-29 07:39

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0020_alter_orderplaced_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='admin',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='app.admin'),
        ),
    ]