# Generated by Django 4.2.3 on 2023-09-23 03:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hook', '0005_conversation_last_image_used'),
    ]

    operations = [
        migrations.CreateModel(
            name='WhiteList',
            fields=[
                ('phone_number', models.CharField(max_length=100, primary_key=True, serialize=False)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]