# Generated by Django 5.0.4 on 2024-06-27 16:03

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0016_product_seller'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name='seller',
            name='email',
        ),
        migrations.RemoveField(
            model_name='seller',
            name='firstname',
        ),
        migrations.RemoveField(
            model_name='seller',
            name='lastname',
        ),
        migrations.RemoveField(
            model_name='seller',
            name='password',
        ),
        migrations.RemoveField(
            model_name='seller',
            name='username',
        ),
        migrations.AddField(
            model_name='seller',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='product',
            name='seller',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]