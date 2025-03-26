from django.forms import ModelForm, Form, FileField, Textarea, BooleanField, CheckboxInput, DateTimeInput, DateInput, TimeInput, CharField, TextInput, IntegerField, NumberInput, DateTimeField, DateField, TimeField, MultipleChoiceField, CheckboxSelectMultiple, ChoiceField
from .models import People, Roles, Projects, Events, EventTypes, Categories, Groups, ViewFamilies, Courses, Semesters, Attendees, ActivityTypes, RolesActivityTypes, Codes, SemesterDates, PeopleSemesters, Activities, Consents, PeopleRoles, Attendance, PeopleEvents


class MyDateInput(DateInput):
    input_type = 'date'


class MyTimeInput(TimeInput):
    input_type = 'time'


class MyDateTimeInput(DateTimeInput):
    input_type = 'datetime-local'


class FilterForm(ModelForm):
    def __init__(self, fields: list[str] = None, values: list[any] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False


class PeopleFilter(FilterForm):
    field_order = ['name', 'surname', 'pcode', 'phone_nr', 'mail', 'is_adult', 'gender', 'country_code', 'description', 'notes']
    is_adult = ChoiceField(label='Czy pełnoletni', choices=(
            ("", ("---------")),
            ("unknown", ("Brak informacji")),
            ("true", ("Tak")),
            ("false", ("Nie")),
        ))

    class Meta:
        model = People
        fields = ['name', 'surname', 'pcode', 'phone_nr', 'mail', 'gender', 'country_code', 'description', 'notes']


class FamilyFilter(Form):
    pid_parent__name = CharField(max_length=20, required=False, widget=TextInput, label="Imię rodzica")
    pid_parent__surname = CharField(max_length=20, required=False, widget=TextInput, label="Nazwisko rodzica")
    pid_parent__pcode = IntegerField(required=False, widget=NumberInput, label="Kod rodzica")
    pid_child__name = CharField(max_length=20, required=False, widget=TextInput, label="Imię dziecka")
    pid_child__surname = CharField(max_length=20, required=False, widget=TextInput, label="Nazwisko dziecka")
    pid_child__pcode = IntegerField(required=False, widget=NumberInput, label="Kod dziecka")


class ActivityFilter(FilterForm):
    field_order = ['activity_type_id', 'full_name', 'date__gte', 'date__lte', 'notes']
    full_name = CharField(max_length=100, required=False, widget=TextInput, label="Osoba")
    date__gte = DateTimeField(required=False, widget=MyDateTimeInput, label="Od")
    date__lte = DateTimeField(required=False, widget=MyDateTimeInput, label="Do")

    class Meta:
        model = Activities
        fields = ['activity_type_id', 'notes']
        widgets = {
            'activity_type_id': TextInput(),
        }


class CourseFilter(FilterForm):
    class Meta:
        model = Courses
        fields = ['name', 'description']


class EventFilter(FilterForm):
    field_order = ['name', 'id_event_type__name', 'date__gte', 'date__lte']
    id_event_type__name = CharField(max_length=50, required=False, widget=TextInput, label="Rodzaj wydarzenia")
    date__gte = DateTimeField(required=False, widget=MyDateTimeInput, label="Start po")
    date__lte = DateTimeField(required=False, widget=MyDateTimeInput, label="Start przed")
    end_date__gte = DateTimeField(required=False, widget=MyDateTimeInput, label="Koniec po")
    end_date__lte = DateTimeField(required=False, widget=MyDateTimeInput, label="Koniec przed")

    class Meta:
        model = Events
        fields = ['name']


class PersonCourseFilter(FilterForm):
    course_id__name = CharField(max_length=50, required=False, widget=TextInput, label="Nazwa kursu")
    name = CharField(max_length=50, required=False, widget=TextInput, label="Nazwa semestru")

    class Meta:
        model = Semesters
        fields = ['name']


class PersonActivitiesFilter(FilterForm):
    field_order = ['activity_type_id', 'full_name', 'date__gte', 'date__lte', 'notes']
    date__gte = DateTimeField(required=False, widget=MyDateTimeInput, label="Od")
    date__lte = DateTimeField(required=False, widget=MyDateTimeInput, label="Do")

    class Meta:
        model = Activities
        fields = ['activity_type_id', 'notes']
        widgets = {
            'activity_type_id': TextInput(),
        }


class CourseSemesterFilter(FilterForm):
    class Meta:
        model = Semesters
        fields = ['name', 'description']


class CodeFilter(FilterForm):
    event_or_activity_type_name = CharField(max_length=50, required=False, widget=TextInput, label="Nazwa rodzaju aktywności/ wydarzenia")
    type = MultipleChoiceField(widget=CheckboxSelectMultiple, choices=(("event_type", "Wydarzenie"), ("activity_type", "Aktywność")), label="Rodzaj", initial=['event_type', 'activity_type'])

    class Meta:
        model = Codes
        fields = ['code']


class SemesterDateFilter(Form):
    date__gte = DateField(required=False, widget=MyDateInput, label="Data od:")
    date__lte = DateField(required=False, widget=MyDateInput, label="Data do:")
    start_time__gte = TimeField(required=False, widget=MyTimeInput, label="Godzina rozpoczęcia od:")
    start_time__lte = TimeField(required=False, widget=MyTimeInput, label="Godzina rozpoczęcia do:")
    end_time__gte = TimeField(required=False, widget=MyTimeInput, label="Godzina zakończenia od:")
    end_time__lte = TimeField(required=False, widget=MyTimeInput, label="Godzina zakończenia do:")


class UpdateableForm(ModelForm):
    def __init__(self, fields: list[str] = None, values: list[any] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def disable(self, fields: list[str]) -> None:
        if '__all' in fields:
            for _, field in self.fields.items():
                field.widget.attrs.update({'disabled': 'true'})
            return
        for field in fields:
            self.fields[field].widget.attrs.update({'disabled': 'true'})


class UploadFileForm(Form):
    file = FileField(label="")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['file'].widget.attrs.update({'accept': '.csv', 'class': 'mb-3'})


class PersonForm(UpdateableForm):
    class Meta:
        model = People
        fields = ['name', 'surname', 'phone_nr', 'mail', 'is_adult', 'gender', 'country_code', 'description', 'notes']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['is_adult'].widget.choices = (
            ("unknown", ("Brak informacji")),
            ("true", ("Tak")),
            ("false", ("Nie")),
        )


class PersonPeopleEventsForm(UpdateableForm):
    class Meta:
        model = PeopleEvents
        exclude = ['id']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.disable(['person_id'])


class EventPeopleEventsForm(UpdateableForm):
    class Meta:
        model = PeopleEvents
        exclude = ['id']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.disable(['event_id'])


class RoleForm(UpdateableForm):
    class Meta:
        model = Roles
        fields = ['role_name']

    def clean(self):
        self.cleaned_data['role_name'] = self.cleaned_data['role_name'].title()
        return super().clean()


class ProjectForm(UpdateableForm):
    class Meta:
        model = Projects
        fields = ['name', 'description']

    def clean(self):
        self.cleaned_data['name'] = self.cleaned_data['name'].title()
        return super().clean()


class EventForm(UpdateableForm):
    class Meta:
        model = Events
        exclude = ['id']
        widgets = {
            'date': MyDateTimeInput(),
            'end_date': MyDateTimeInput()
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['description'].widget = Textarea(attrs={'name': 'description_body', 'class': 'form-control', 'rows': '3'})

    def clean(self):
        self.cleaned_data['name'] = self.cleaned_data['name'].title()
        return super().clean()


class EventTypeForm(UpdateableForm):
    class Meta:
        model = EventTypes
        fields = ['name']

    def clean(self):
        self.cleaned_data['name'] = self.cleaned_data['name'].title()
        return super().clean()


class CategoriesForm(UpdateableForm):
    class Meta:
        model = Categories
        fields = ['name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs.update({'class': 'form-control', 'type': 'text'})
        self.fields['name'].label = "Nazwa"
        self.fields['name'].help_text = "Nazwa może mieć maksymalną długość 20 znaków"


class GroupsForm(UpdateableForm):
    class Meta:
        model = Groups
        fields = ['name', 'category']


class ViewFamiliesForm(UpdateableForm):
    class Meta:
        model = ViewFamilies
        exclude = ['id']


class CoursesForm(UpdateableForm):
    class Meta:
        model = Courses
        exclude = ['id']

    def clean(self):
        self.cleaned_data['name'] = self.cleaned_data['name'].title()
        return super().clean()


class SemesterForm(UpdateableForm):
    class Meta:
        model = Semesters
        fields = ['course_id', 'name', 'description']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['description'].widget = Textarea(attrs={'name': 'description_body', 'class': 'form-control', 'rows': '3'})

    def clean(self):
        self.cleaned_data['name'] = self.cleaned_data['name'].title()
        return super().clean()


class SemesterFormEdit(UpdateableForm):
    class Meta:
        model = Semesters
        fields = ['course_id', 'name', 'description']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['description'].widget = Textarea(attrs={'name': 'description_body', 'class': 'form-control', 'rows': '3'})
        self.fields['course_id'].widget.attrs.update({'disabled': 'True'})

    def clean(self):
        self.cleaned_data['name'] = self.cleaned_data['name'].title()
        return super().clean()


class AttendeesForm(UpdateableForm):
    class Meta:
        model = Attendees
        exclude = ['id']


class AttendeesFormEdit(UpdateableForm):
    class Meta:
        model = Attendees
        exclude = ['id', 'event', 'group']


class ActivityTypesForm(UpdateableForm):
    class Meta:
        model = ActivityTypes
        exclude = ['id', 'allowed_roles']

    def clean(self):
        self.cleaned_data['name'] = self.cleaned_data['name'].title()
        return super().clean()


class RolesActivityTypesForm(UpdateableForm):
    class Meta:
        model = RolesActivityTypes
        exclude = ['id']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rid'].label = "Rola"
        self.fields['atid'].label = "Rodzaj aktywności"


class CodesForm(UpdateableForm):
    class Meta:
        model = Codes
        exclude = ['id', 'cid']

    def clean(self):
        self.cleaned_data['code'] = self.cleaned_data['code'].upper()
        return super().clean()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['additional_checks'].widget = Textarea(attrs={'name': 'description_body', 'class': 'form-control', 'rows': '3'})


class SemesterDatesForm(UpdateableForm):
    class Meta:
        model = SemesterDates
        exclude = ['id', 'date_id']
        widgets = {
            'date': MyDateInput(),
            'start_time': MyTimeInput(),
            'end_time': MyTimeInput()
            }


class PeopleSemestersForm(UpdateableForm):
    class Meta:
        model = PeopleSemesters
        exclude = ['id']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['course_id'].widget.attrs.update({'id': 'course', 'onchange': 'toggleChange()'})
        self.fields['semester_id'].widget.attrs.update({'id': 'semester', 'disabled': 'true'})


class ConsentsForm(UpdateableForm):
    field_order = ['person_id', 'activity_type_id', 'activity_id', 'address', 'notes']

    class Meta:
        model = Consents
        exclude = ['id', 'consent_id']


class ActivitiesForm(UpdateableForm):
    checkbox = BooleanField(required=False, label="Dołącz kurs do aktywności", widget=CheckboxInput(
        attrs={'type': 'checkbox', 'onchange': 'toggleDisabled(this.checked, ["course", "semester"])', 'id': 'checkbox'}
    ))
    field_order = ['activity_type_id', 'person_id', 'notes', 'checkbox', 'course_id', 'semester_id']

    class Meta:
        model = Activities
        exclude = ['id', 'activity_id']
        widgets = {
            'date': MyDateTimeInput()  # TODO add to template
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'person_id' in self.initial.keys():
            self.fields['activity_type_id'].queryset = ActivityTypes.objects.filter(
                allowed_roles__in=Roles.objects.filter(
                    plp_w_roles__in=People.objects.filter(id=self.initial['person_id'])
                )
            )
        self.fields['notes'].widget = Textarea(attrs={'name': 'notes_body', 'class': 'form-control', 'rows': '3'})
        if 'instance' not in kwargs.keys() or not kwargs['instance'].course_id:
            self.disable(['course_id', 'semester_id'])
        elif 'instance' in kwargs.keys():
            self.fields['checkbox'].widget.attrs.update({'checked': '1'})
        self.fields['course_id'].widget.attrs.update({'id': 'course', 'onchange': 'toggleChange()'})
        self.fields['semester_id'].widget.attrs.update({'id': 'semester'})


class ActivitiesViewForm(UpdateableForm):
    class Meta:
        model = Activities
        fields = ['activity_type_id', 'notes']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['notes'].widget = Textarea(attrs={'name': 'notes_body', 'class': 'form-control', 'rows': '3'})


class GrantRoleForm(UpdateableForm):
    class Meta:
        model = PeopleRoles
        exclude = ['id']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rid'].label = "Rola"
        self.fields['pid'].label = "Osoba"


class EditAttendanceFromDate(UpdateableForm):
    class Meta:
        model = Attendance
        fields = ['person_id', 'attendance_type']


class EditAttendanceFromPerson(UpdateableForm):
    class Meta:
        model = Attendance
        fields = ['date_id', 'attendance_type']


class ReportForm(Form):
    since = DateField(label="Od", widget=MyDateInput())
    to = DateField(label="Do", widget=MyDateInput())
