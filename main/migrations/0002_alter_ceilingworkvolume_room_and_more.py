# Generated by Django 5.0.6 on 2024-12-02 12:55

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ceilingworkvolume',
            name='room',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ceilingworkvolume_volumes', to='main.room'),
        ),
        migrations.AlterField(
            model_name='floorworkvolume',
            name='room',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='floorworkvolume_volumes', to='main.room'),
        ),
        migrations.AlterField(
            model_name='wallworkvolume',
            name='room',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='wallworkvolume_volumes', to='main.room'),
        ),
    ]
