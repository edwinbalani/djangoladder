# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-13 19:28
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Ladder', '0003_auto_20170213_1410'),
    ]

    operations = [
        migrations.AddField(
            model_name='player',
            name='player_password',
            field=models.CharField(default='', max_length=300),
        ),
    ]
