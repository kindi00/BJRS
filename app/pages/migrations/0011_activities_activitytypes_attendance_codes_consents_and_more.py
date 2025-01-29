# Generated by Django 5.0.4 on 2024-10-29 23:46

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0010_courses_alter_atendees_table_alter_peopleroles_table'),
    ]

    operations = [
        migrations.CreateModel(
            name='Activities',
            fields=[
                ('id', models.IntegerField(db_column='dummy', primary_key=True, serialize=False)),
                ('activity_id', models.IntegerField(db_column='activity_id', default=1, unique=True)),
                ('date', models.DateTimeField(auto_now=True, db_column='date', max_length=2000)),
                ('notes', models.CharField(blank=True, db_column='notes', max_length=2000, null=True)),
            ],
            options={
                'db_table': 'view_activities',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='ActivityTypes',
            fields=[
                ('id', models.SmallAutoField(db_column='id', primary_key=True, serialize=False)),
                ('name', models.CharField(db_column='name', max_length=20, unique=True)),
            ],
            options={
                'db_table': 'activity_types',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Attendance',
            fields=[
                ('id', models.IntegerField(db_column='dummy', default=1, primary_key=True, serialize=False, verbose_name=django.db.models.deletion.CASCADE)),
                ('attendance_type', models.CharField(db_column='attendance_type', max_length=1)),
            ],
            options={
                'db_table': 'view_attendance',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Codes',
            fields=[
                ('id', models.IntegerField(db_column='dummy', default=1, primary_key=True, serialize=False)),
                ('cid', models.IntegerField(db_column='id', null=True, verbose_name=django.db.models.deletion.CASCADE)),
                ('code', models.CharField(max_length=20)),
            ],
            options={
                'db_table': 'view_codes',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Consents',
            fields=[
                ('id', models.IntegerField(db_column='dummy', primary_key=True, serialize=False)),
                ('consent_id', models.IntegerField(db_column='consent_id', default=1)),
                ('address', models.CharField(db_column='address', max_length=200)),
                ('notes', models.CharField(blank=True, db_column='notes', max_length=2000, null=True)),
            ],
            options={
                'db_table': 'view_consents',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='PeopleSemesters',
            fields=[
                ('id', models.IntegerField(db_column='dummy', default=1, primary_key=True, serialize=False)),
            ],
            options={
                'db_table': 'view_people_semesters',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='RolesActivityTypes',
            fields=[
                ('id', models.IntegerField(db_column='dummy', default=1, primary_key=True, serialize=False, verbose_name=django.db.models.deletion.CASCADE)),
            ],
            options={
                'db_table': 'view_roles_activity_types',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='SelectAtendees',
            fields=[
                ('category', models.CharField(db_column='category', primary_key=True, serialize=False)),
                ('no_atendees', models.IntegerField(db_column='no_atendees')),
            ],
            options={
                'db_table': 'select_atendees',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='SemesterDates',
            fields=[
                ('id', models.IntegerField(db_column='dummy', default=1, primary_key=True, serialize=False)),
                ('date_id', models.IntegerField(db_column='date_id', unique=True)),
                ('date', models.DateField(db_column='date')),
                ('start_time', models.TimeField(db_column='start_time')),
                ('end_time', models.TimeField(db_column='end_time')),
            ],
            options={
                'db_table': 'view_semester_dates',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Semesters',
            fields=[
                ('dummy', models.IntegerField(db_column='dummy', default=1, primary_key=True, serialize=False)),
                ('id', models.IntegerField(db_column='id', unique=True)),
                ('name', models.CharField(db_column='name', max_length=50)),
                ('description', models.CharField(blank=True, db_column='description', max_length=2000, null=True)),
            ],
            options={
                'db_table': 'view_semesters',
                'managed': False,
            },
        ),
    ]
