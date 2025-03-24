# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from django.core.validators import MinValueValidator

LAN_PLP_NAME = "Imię"
LAN_PLP_SURNAME = "Nazwisko"
LAN_PLP_PHONE = "Telefon"
LAN_PLP_GENDER = "Płeć"
LAN_PLP_COUNTRY = "Kraj"
LAN_PLP_DESC = "Cecha charakterystyczna"
LAN_PLP_NOTES = "Uwagi"
LAN_FAM_PARENT = "Rodzic"
LAN_FAM_CHILD = "Dziecko"
LAN_ROL_NAME = "Nazwa roli"
LAN_ROL_PLP = "Role osób"
LAN_PRO_NAME = "Nazwa projektu"
LAN_PRO_DESC = "Opis projektu"


class Attendees(models.Model):
    id = models.IntegerField(primary_key=True, db_column="dummy", default=1)
    event = models.ForeignKey('Events', models.DO_NOTHING, db_column='event_id', verbose_name="Wydarzenie")
    group = models.ForeignKey('Groups', models.DO_NOTHING, db_column='group_id', verbose_name="Grupa")
    no_attendees = models.IntegerField(db_column='no_atendees', verbose_name="Liczba uczestników", validators=[MinValueValidator(0, "Liczba uczestników nie może być mniejsza niż 0")])

    class Meta:
        managed = False
        db_table = 'view_atendees'
        constraints = [
            models.CheckConstraint(
                name="non_negative_no_attendees",
                check=models.Q(no_attendees__gte=0),
                violation_error_message="Liczba uczestników nie może być mniejsza niż 0"
            )
        ]

    def __str__(self) -> str:
        return f"Uczestnicy z grupy \"{self.group}\" na wydarzeniu \"{self.event}\""


class ActivityTypes(models.Model):
    id = models.SmallAutoField(primary_key=True, db_column='id')
    name = models.CharField(max_length=50, unique=True, db_column='name', verbose_name='Nazwa')
    allowed_roles = models.ManyToManyField('Roles', through='RolesActivityTypes')

    class Meta:
        managed = False
        db_table = 'activity_types'

    def __str__(self) -> str:
        return self.name


class AttendanceTypes(models.Model):
    id = models.SmallAutoField(primary_key=True, db_column='id')
    name = models.CharField(max_length=20, unique=True, db_column='name')

    class Meta:
        managed = False
        db_table = 'attendance_types'

    def __str__(self) -> str:
        return self.name


class Activities(models.Model):
    id = models.IntegerField(primary_key=True, db_column='dummy')
    activity_id = models.IntegerField(db_column='activity_id', default=1, unique=True)
    activity_type_id = models.ForeignKey('ActivityTypes', models.DO_NOTHING, db_column='activity_type_id', verbose_name='Rodzaj aktywności')
    person_id = models.ForeignKey('People', models.DO_NOTHING, db_column='person_id', verbose_name='Osoba')
    date = models.DateTimeField(max_length=2000, db_column='date', auto_now=True, verbose_name='Data')
    notes = models.CharField(max_length=2000, blank=True, null=True, db_column='notes', verbose_name='Opis')
    course_id = models.ForeignKey('Courses', models.SET_NULL, db_column='course_id', null=True, blank=True, verbose_name='Kurs')
    semester_id = models.ForeignKey('Semesters', models.SET_NULL, db_column='semester_id', to_field='id', null=True, blank=True, verbose_name='Semestr')

    class Meta:
        managed = False
        db_table = 'view_activities'
        constraints = [
            models.UniqueConstraint(
                fields=['activity_id', 'activity_type_id', 'person_id'], name='unique_activity_activity_type_person_combination'
            ),
            models.CheckConstraint(
                check=models.Q(course_id__isnull=False) & models.Q(semester_id__isnull=False) | models.Q(course_id__isnull=True) & models.Q(semester_id__isnull=True),
                name='semester_and_course'
            )
        ]

    def __str__(self) -> str:
        return f"{self.activity_type_id} {self.date}"


class Codes(models.Model):
    id = models.IntegerField(primary_key=True, db_column="dummy", default=1)
    project_id = models.ForeignKey('Projects', models.CASCADE, db_column='project_id', verbose_name="Projekt")
    cid = models.IntegerField(models.CASCADE, db_column='id', null=True)
    event_type = models.ForeignKey('EventTypes', models.CASCADE, null=True, blank=True, verbose_name="Rodzaj wydarzenia")
    activity_type = models.ForeignKey('ActivityTypes', models.CASCADE, null=True, blank=True, verbose_name="Rodzaj aktywności")
    code = models.CharField(max_length=20, verbose_name="Kod")
    additional_checks = models.CharField(max_length=2000, verbose_name="Dodatkowe warunki", null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'view_codes'
        constraints = [
            models.UniqueConstraint(
                fields=['project_id', 'cid'], name='unique_project_id_cid_combination'
            ),
            models.CheckConstraint(
                check=models.Q(event_type__isnull=False) & models.Q(activity_type__isnull=True) | models.Q(event_type__isnull=True) & models.Q(activity_type__isnull=False),
                name='event_or_activity_type'
            )
        ]

    def __str__(self) -> str:
        return self.code

    def type(self):
        if self.activity_type is None:
            return "Wydarzenie"
        return "Aktywność"

    def name(self):
        if self.activity_type is None:
            return self.event_type
        return self.activity_type


class RolesActivityTypes(models.Model):
    id = models.IntegerField(models.CASCADE, db_column='dummy', primary_key=True, default=1)
    rid = models.ForeignKey('Roles', models.CASCADE, db_column='rid', related_name='roles_activity_types_rid')
    atid = models.ForeignKey('ActivityTypes', models.CASCADE, db_column='atid', related_name='roles_activity_types_atid')

    class Meta:
        managed = False
        db_table = 'view_roles_activity_types'
        constraints = [
            models.UniqueConstraint(
                fields=['rid', 'atid'], name='unique_rid_atid_combination'
            )
        ]


class SelectAttendees(models.Model):
    category = models.CharField(primary_key=True, db_column="category")
    event = models.ForeignKey('Events', models.DO_NOTHING, db_column='event_id')
    group = models.ForeignKey('Groups', models.DO_NOTHING, db_column='group_id')
    no_attendees = models.IntegerField(db_column='no_atendees')

    class Meta:
        managed = False
        db_table = 'select_atendees'


class Categories(models.Model):
    id = models.SmallAutoField(primary_key=True)
    name = models.CharField(unique=True, max_length=50)

    class Meta:
        managed = False
        db_table = 'categories'

    def __str__(self) -> str:
        return self.name


class Courses(models.Model):
    id = models.SmallAutoField(primary_key=True, db_column='id')
    name = models.CharField(max_length=50, blank=True, null=True, db_column='name', verbose_name="Nazwa", unique=True)
    teacher_id = models.ForeignKey('People', models.SET_NULL, db_column='teacher_id', null=True, blank=True, verbose_name="Nauczyciel")
    description = models.CharField(max_length=2000, blank=True, null=True, db_column='description', verbose_name="Opis")

    class Meta:
        managed = False
        db_table = 'courses'

    def __str__(self) -> str:
        return self.name


class Consents(models.Model):
    id = models.IntegerField(primary_key=True, db_column='dummy')
    person_id = models.ForeignKey('People', models.CASCADE, db_column='person_id', related_name='consents_person_set', verbose_name='Osoba')
    consent_id = models.IntegerField(db_column='consent_id', default=1)
    activity_id = models.ForeignKey('Activities', models.CASCADE, db_column='activity_id', to_field='activity_id', null=True, blank=True, verbose_name='Aktywność')
    activity_type_id = models.ForeignKey('ActivityTypes', models.CASCADE, db_column='activity_type_id', null=True, blank=True, verbose_name='Rodzaj aktywności')
    address = models.CharField(max_length=200, db_column='address', verbose_name='Miejsce przechowywania')
    notes = models.CharField(max_length=2000, db_column='notes', null=True, blank=True, verbose_name='Uwagi')

    class Meta:
        managed = False
        db_table = 'view_consents'
        constraints = [
            models.UniqueConstraint(
                fields=['person_id', 'consent_id'], name='unique_person_id_consent_id_combination'
            ),
            models.UniqueConstraint(
                fields=['activity_id', 'activity_type_id'], name='unique_activity_pk_combination'
            )
        ]


class Semesters(models.Model):
    dummy = models.IntegerField(primary_key=True, db_column='dummy', default=1)
    id = models.IntegerField(db_column='id', unique=True)
    name = models.CharField(max_length=50, db_column='name', verbose_name="Nazwa")
    course_id = models.ForeignKey('Courses', models.DO_NOTHING, db_column='course_id', verbose_name="Kurs")
    description = models.CharField(max_length=2000, db_column='description', null=True, blank=True, verbose_name="Opis")

    class Meta:
        managed = False
        db_table = 'view_semesters'
        constraints = [
            models.UniqueConstraint(fields=['id', 'course_id'], name='unique_semester')
        ]

    def __str__(self) -> str:
        return self.name


class EventTypes(models.Model):
    id = models.SmallAutoField(primary_key=True)
    name = models.CharField(unique=True, max_length=50, verbose_name="Nazwa rodzaju wydarzenia")

    class Meta:
        managed = False
        db_table = 'event_types'

    def __str__(self) -> str:
        return self.name


class Events(models.Model):
    id = models.SmallAutoField(primary_key=True)
    name = models.CharField(max_length=50, verbose_name="Nazwa", unique=True)
    date = models.DateTimeField(blank=True, null=True, verbose_name="Data")
    no_attendees = models.SmallIntegerField(db_column='no_atendees', verbose_name="Liczba uczestników", validators=[MinValueValidator(0, "Liczba uczestników nie może być mniejsza niż 0")])
    description = models.CharField(max_length=2000, blank=True, null=True, verbose_name="Opis")
    id_event_type = models.ForeignKey(EventTypes, models.CASCADE, db_column='id_event_type', verbose_name="Rodzaj wydarzenia")

    class Meta:
        managed = False
        db_table = 'events'
        constraints = [
            models.CheckConstraint(
                name="non_negative_events_no_attendees",
                check=models.Q(no_attendees__gte=0),
                violation_error_message="Liczba uczestników nie może być mniejsza niż 0"
            )
        ]

    def __str__(self) -> str:
        return self.name


class Groups(models.Model):
    id = models.SmallAutoField(primary_key=True)
    name = models.CharField(unique=True, max_length=50, verbose_name="Nazwa")
    category = models.ForeignKey(Categories, models.DO_NOTHING, blank=True, null=True, verbose_name="Kategoria")

    class Meta:
        managed = False
        db_table = 'groups'

    def __str__(self) -> str:
        return self.name


class Projects(models.Model):
    id = models.SmallAutoField(primary_key=True, db_column="prid")
    name = models.CharField(verbose_name=LAN_PRO_NAME, db_column="name", max_length=50, unique=True)
    description = models.CharField(verbose_name=LAN_PRO_DESC, db_column="description", max_length=200, null=True, blank=True)

    class Meta:
        managed = False
        db_table = "projects"

    def __str__(self) -> str:
        return self.name


class PeopleRoles(models.Model):
    id = models.IntegerField(primary_key=True, db_column="dummy", default=1)
    rid = models.ForeignKey('Roles', models.CASCADE, db_column='rid')
    pid = models.ForeignKey('People', models.CASCADE, db_column='pid')

    class Meta:
        managed = False
        db_table = 'view_plp_roles'
        constraints = [
            models.UniqueConstraint(fields=['rid', 'pid'], name='unique_role_people')
        ]


class PeopleSemesters(models.Model):
    id = models.IntegerField(primary_key=True, db_column="dummy", default=1)
    course_id = models.ForeignKey('Courses', models.CASCADE, db_column='course_id', verbose_name="Kurs")
    semester_id = models.ForeignKey('Semesters', models.DO_NOTHING, db_column='semester_id', to_field='id', related_name='plp_semesters_semester_id_set', verbose_name="Semestr")
    person_id = models.ForeignKey('People', models.CASCADE, db_column='person_id', verbose_name="Uczestnik")

    class Meta:
        managed = False
        db_table = 'view_people_semesters'
        constraints = [
            models.UniqueConstraint(fields=['course_id', 'semester_id', 'person_id'], name='unique_people_semester')
        ]

    def __str__(self) -> str:
        return f"Uczestnictwo {self.person_id} w semestrze {self.semester_id} kursu {self.course_id}"


class PeopleEvents(models.Model):
    id = models.IntegerField(primary_key=True, db_column="dummy", default=1)
    event_id = models.ForeignKey('Events', models.CASCADE, db_column='event_id', verbose_name="Wydarzenie")
    person_id = models.ForeignKey('People', models.CASCADE, db_column='person_id', verbose_name="Uczestnik")
    attendance_type = models.ForeignKey('AttendanceTypes', models.CASCADE, db_column='attendance_type', verbose_name='Rodzaj obecności', null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'view_people_events'
        constraints = [
            models.UniqueConstraint(fields=['event_id', 'person_id'], name='unique_people_events')
        ]

    def __str__(self) -> str:
        return f"Uczestnictwo {self.person_id} w wydarzeniu {self.event_id}"


class Roles(models.Model):
    id = models.SmallAutoField(primary_key=True, db_column='rid')
    role_name = models.CharField(verbose_name=LAN_ROL_NAME, db_column='role_name', max_length=50)
    plp_w_roles = models.ManyToManyField('People', verbose_name=LAN_ROL_PLP, through=PeopleRoles)

    class Meta:
        managed = False
        db_table = 'roles'
        constraints = [
            models.UniqueConstraint(fields=['role_name'], name='unique_role_name')
        ]

    def __str__(self) -> str:
        return self.role_name


class Families(models.Model):
    id = models.BigAutoField(primary_key=True)
    pid_parent = models.ForeignKey('People', models.CASCADE, verbose_name=LAN_FAM_PARENT, db_column='pid_parent', related_name='families_pid_parent_set')
    pid_child = models.ForeignKey('People', models.CASCADE, verbose_name=LAN_FAM_CHILD, db_column='pid_child', related_name='families_pid_child_set')

    class Meta:
        managed = False
        db_table = 'families'
        constraints = [
            models.UniqueConstraint(
                fields=['pid_parent', 'pid_child'], name='unique_pid_parent_pid_child_combination'
            )
        ]


class ViewFamilies(models.Model):
    id = models.IntegerField(models.CASCADE, db_column='dummy', primary_key=True, default=1)
    pid_parent = models.ForeignKey('People', models.CASCADE, verbose_name=LAN_FAM_PARENT, db_column='pid_parent', related_name='vfamilies_pid_parent_set')
    pid_child = models.ForeignKey('People', models.CASCADE, verbose_name=LAN_FAM_CHILD, db_column='pid_child', related_name='vfamilies_pid_child_set')

    class Meta:
        managed = False
        db_table = 'view_family'
        constraints = [
            models.UniqueConstraint(
                fields=['pid_parent', 'pid_child'], name='vunique_pid_parent_pid_child_combination'
            )
        ]


class SemesterDates(models.Model):
    id = models.IntegerField(db_column='dummy', primary_key=True, default=1)
    course_id = models.ForeignKey('Courses', models.CASCADE, db_column='course_id', related_name='sem_dates_course_id', verbose_name='Kurs')
    semester_id = models.ForeignKey('Semesters', models.DO_NOTHING, to_field='id', db_column='semester_id', related_name='sem_dates_semester_id', verbose_name='Semestr')
    date_id = models.IntegerField(db_column='date_id', unique=True)
    date = models.DateField(db_column='date', verbose_name='Data')
    start_time = models.TimeField(db_column='start_time', verbose_name='Godzina rozpoczęcia')
    end_time = models.TimeField(db_column='end_time', verbose_name='Godzina zakończenia')

    class Meta:
        managed = False
        db_table = 'view_semester_dates'
        constraints = [
            models.UniqueConstraint(
                fields=['course_id', 'semester_id', 'date_id'], name='course_semester_data_id_unique_set'
            ),
            models.CheckConstraint(
                name="end_after_start",
                check=models.Q(end_time__gt=models.F('start_time')),
                violation_error_message="Termin kursu nie może się zakończyć przed rozpoczęciem"
            )
        ]

    def __str__(self) -> str:
        return f"{self.date} {self.start_time}-{self.end_time}"


class Attendance(models.Model):
    id = models.IntegerField(models.CASCADE, db_column='dummy', primary_key=True, default=1)
    course_id = models.ForeignKey('Courses', models.CASCADE, db_column='course_id', related_name='attendance_course_id')
    semester_id = models.ForeignKey('Semesters', models.DO_NOTHING, to_field='id', db_column='semester_id', related_name='att_dates_semester_id')
    date_id = models.ForeignKey('SemesterDates', models.DO_NOTHING, to_field='date_id', db_column='date_id', related_name='attendance_date_id')
    person_id = models.ForeignKey('People', models.CASCADE, db_column='person_id', related_name='attendance_person_id')
    attendance_type = models.ForeignKey('AttendanceTypes', models.CASCADE, db_column='attendance_type', related_name='attendance_type', null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'view_attendance'
        constraints = [
            models.UniqueConstraint(
                fields=['course_id', 'semester_id', 'date_id', 'person_id'], name='att_course_semester_data_person_id_unique_set'
            )
        ]


class Genders(models.Model):
    id = models.SmallAutoField(primary_key=True, db_column='id')
    name = models.CharField(max_length=20, unique=True, db_column='name')

    class Meta:
        managed = False
        db_table = 'genders'

    def __str__(self):
        return self.name


class People(models.Model):
    id = models.SmallAutoField(primary_key=True, db_column='pid')
    name = models.CharField(LAN_PLP_NAME, max_length=50)
    surname = models.CharField(LAN_PLP_SURNAME, max_length=50)
    pcode = models.SmallIntegerField('Kod', null=True, validators=[MinValueValidator(1, "Kod nie może być mniejszy niż 1")])
    phone_nr = models.CharField(LAN_PLP_PHONE, max_length=15, blank=True, null=True)
    mail = models.CharField(max_length=50, unique=True)
    is_adult = models.BooleanField(verbose_name='Czy pełnoletni', blank=True, null=True)
    gender = models.ForeignKey('Genders', on_delete=models.DO_NOTHING, verbose_name=LAN_PLP_GENDER, blank=True, null=True, db_column='gender')
    country_code = models.CharField(LAN_PLP_COUNTRY, max_length=30, blank=True, null=True)
    description = models.CharField(LAN_PLP_DESC, max_length=50, blank=True, null=True)
    notes = models.CharField(LAN_PLP_NOTES, max_length=200, blank=True, null=True)
    parents = models.ManyToManyField('self', verbose_name=LAN_FAM_PARENT, through=ViewFamilies, through_fields=('pid_child', 'pid_parent'), symmetrical=False)

    class Meta:
        managed = False
        db_table = 'people'

    def __str__(self) -> str:
        if self.pcode is None:
            return f"{self.name} {self.surname}"
        return f"{self.name} {self.surname} {self.pcode}"
