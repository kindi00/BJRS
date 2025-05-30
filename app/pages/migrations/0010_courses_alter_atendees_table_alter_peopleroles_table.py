# Generated by Django 5.0.4 on 2024-09-17 13:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0009_atendees_categories_events_eventtypes_groups_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Courses',
            fields=[
                ('id', models.SmallAutoField(db_column='id', primary_key=True, serialize=False)),
                ('name', models.CharField(blank=True, db_column='name', max_length=50, null=True)),
                ('description', models.CharField(blank=True, db_column='description', max_length=2000, null=True)),
            ],
            options={
                'db_table': 'courses',
                'managed': False,
            },
        ),
        migrations.AlterModelTable(
            name='atendees',
            table='view_atendees',
        ),
        migrations.AlterModelTable(
            name='peopleroles',
            table='view_plp_roles',
        ),
    ]
