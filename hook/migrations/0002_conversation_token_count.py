# Generated by Django 4.2.3 on 2023-08-08 10:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hook', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='conversation',
            name='token_count',
            field=models.IntegerField(default=0),
        ),
    ]