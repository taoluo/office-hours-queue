# Generated by Django 2.2.7 on 2020-02-22 16:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_auto_20200218_0013'),
    ]

    operations = [
        migrations.AddField(
            model_name='queue',
            name='active_override_time',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]