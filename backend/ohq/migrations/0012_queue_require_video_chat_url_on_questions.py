# Generated by Django 3.1.7 on 2021-09-17 16:29

from django.db import migrations, models


def populate_require_url_in_queue(apps, schema_editor):
    Queue = apps.get_model("ohq", "Queue")
    for queue in Queue.objects.all():
        queue.video_chat_setting = (
            "required" if queue.course.require_video_chat_url_on_questions else "disabled"
        )
        queue.save()


class Migration(migrations.Migration):

    dependencies = [
        ("ohq", "0011_merge_20210415_2110"),
    ]

    operations = [
        migrations.AddField(
            model_name="queue",
            name="video_chat_setting",
            field=models.CharField(
                choices=[
                    ("REQUIRED", "required"),
                    ("OPTIONAL", "optional"),
                    ("DISABLED", "disabled"),
                ],
                default="OPTIONAL",
                max_length=8,
            ),
        ),
        migrations.RunPython(populate_require_url_in_queue),
    ]