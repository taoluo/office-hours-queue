# Generated by Django 2.2.7 on 2020-02-03 18:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0011_auto_20200203_1638'),
    ]

    operations = [
        migrations.AddField(
            model_name='feedbackquestion',
            name='required',
            field=models.BooleanField(default=True),
        ),
    ]