# Generated by Django 4.2.3 on 2023-08-08 04:44

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Conversation',
            fields=[
                ('phone_number', models.CharField(max_length=100, primary_key=True, serialize=False)),
                ('context', models.CharField(max_length=1024)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
