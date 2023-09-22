# Generated by Django 4.2.3 on 2023-09-22 10:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hook', '0002_conversation_token_count'),
    ]

    operations = [
        migrations.AddField(
            model_name='conversation',
            name='is_subscribed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='conversation',
            name='last_token_used',
            field=models.DateTimeField(default=None),
        ),
    ]
