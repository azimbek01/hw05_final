# Generated by Django 2.2.9 on 2020-04-19 17:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0003_auto_20200417_2112'),
    ]

    operations = [
        migrations.AlterField(
            model_name='group',
            name='slug',
            field=models.SlugField(max_length=40, unique=True),
        ),
    ]
