# Generated by Django 4.2.3 on 2023-11-10 08:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hook', '0007_todo'),
    ]

    operations = [
        migrations.AddField(
            model_name='conversation',
            name='last_message_id',
            field=models.CharField(default=None, max_length=100, null=True),
        ),
    ]
