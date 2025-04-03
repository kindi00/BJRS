from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from .forms import ModelForm, PersonForm, RoleForm, ProjectForm, UploadFileForm, EventForm, EventTypeForm, CategoriesForm, GroupsForm, ViewFamiliesForm, CoursesForm, SemesterForm, AttendeesForm, AttendeesFormEdit, SemesterFormEdit, ActivityTypesForm, RolesActivityTypesForm, CodesForm, SemesterDatesForm, PeopleSemestersForm, ActivitiesForm, ActivitiesViewForm, ConsentsForm, GrantRoleForm, EditAttendanceFromDate, EditAttendanceFromPerson, PersonPeopleEventsForm, EventPeopleEventsForm, PeopleFilter, FamilyFilter, ActivityFilter, CourseFilter, EventFilter, PersonCourseFilter, PersonActivitiesFilter, CourseSemesterFilter, SemesterDateFilter, CodeFilter, ReportForm
from .models import People, Roles, Projects, Events, EventTypes, Categories, Groups, ViewFamilies, PeopleRoles, Courses, Semesters, Attendees, SelectAttendees, ActivityTypes, RolesActivityTypes, Codes, SemesterDates, Attendance, PeopleSemesters, Activities, Consents, PeopleEvents, Genders
from django.db import connection
from django.db.models import Q, Model, Value, CharField, Count, Sum
from django.db.models.functions import Concat
from csv import DictReader, writer
from io import TextIOWrapper
from dataclasses import dataclass
from django.http import FileResponse
import os


@dataclass
class NavItem:
    name: str
    href: str = '#'
    isActive: bool = False
    isDisabled: bool = False
    """ overrides isActive """


@dataclass
class HeaderCell:
    name: str
    index: int = 0
    id: str = ''
    isSortable: str = ''


@dataclass
class DataCell:
    type: str
    """ One of: 'data', 'link', 'date', 'time', 'datetime' """
    data: any


@dataclass
class Link:
    name: str
    linkClass: str
    href: str


@dataclass
class Button:
    name: str
    href: str
    # target: str


@dataclass
class HTMLRow:
    fields: list[DataCell]
    onclick: str = '#'
    id: str = -1


@dataclass
class HTMLTable:
    header_cells: list[HeaderCell]
    rows: list[HTMLRow]
    body_name: str = ''


@dataclass
class Filter:
    name: str
    id: str
    placeholder: str = ''
    value: str = ''


def map_is_adult(input: str) -> bool:
    try:
        return {
            'tak': True,
            'pelnoletni': True,
            'pełnoletni': True,
            'nie': False,
            'niepelnoletni': False,
            'niepełnoletni': False,
            'brak_informacji': None,
        }[input]
    except KeyError:
        return None


def find_delimeter(header: str) -> str:
    delimeter = ';'
    for d in [',', ';', ':']:
        if d in header:
            delimeter = d
    return delimeter


def read_input(file: str) -> list[dict]:
    rows = TextIOWrapper(file, encoding='utf-8', newline="")
    delimeter = find_delimeter(rows.readline())
    rows.seek(0, 0)
    return [row for row in DictReader(rows, delimiter=delimeter)]


def format_filter_query(query: dict):
    output = {}
    for key, value in query.items():
        if value != '':
            if key.split('__')[-1] in ['gte', 'lte']:
                output[key] = value
            else:
                output[key + '__icontains'] = value
    return output


class NavigationBar:
    nav_bars: list[list[NavItem]] = ...
    active_nav_items: list[str] = ...

    def _activate_nav_item(self):
        for i, nav_items in enumerate(self.nav_bars):
            for item in nav_items:
                if item.name != self.active_nav_items[i]:
                    item.isActive = False
                    continue
                item.isActive = True

    def _set_nav_bars(self, instances, first_setable_bar=1, **kwargs):
        d = {
            0: 'fpk',
            1: 'spk',
            2: 'tpk'
        }
        output = self.nav_bars[:first_setable_bar]
        for i, nav_bar in enumerate(self.nav_bars[first_setable_bar:]):
            data_items = [NavItem(item.name, item.href % tuple([kwargs[d[x]] for x in range(i+1)]), item.isActive) for item in nav_bar]
            output += [[NavItem(instances[i], isDisabled=True)] + data_items]
        return output


BROWSE_NAV_ITEMS = [
    NavItem("Osoby", "/browse/people"),
    NavItem("Rodziny", "/browse/families"),
    NavItem("Role", "/browse/roles"),
    NavItem("Aktywności", "/browse/activites"),
    NavItem("Kursy Językowe", "/browse/courses"),
    NavItem("Projekty", "/browse/projects"),
    NavItem("Wydarzenia", "/browse/events")
]


ACTIVITIES_NAV_ITEMS = [
    NavItem("Przeglądaj", "/browse/activites"),
    NavItem("Rodzaje aktywności", "/browse/activity_types"),
]


EVENT_NAV_ITEMS = [
    NavItem("Przeglądaj", "/browse/events"),
    NavItem("Rodzaje wydarzeń", "/browse/event_types"),
    NavItem("Grupy uczestników", "/browse/categories")
]


CON_EVENT_NAV_ITEMS = [
    NavItem("Dane", "/events/%s/data"),
    NavItem("Szczegóły o uczestnikach", "/events/%s/attendees"),
    NavItem("Obecność", "/events/%s/attendance")
]


ROLES_NAV_ITEMS = [
    NavItem("Osoby z rolą", "/roles/%s/data"),
    NavItem("Dozwolone aktywności", "/roles/%s/browse")
]


COURSES_NAV_ITEMS = [
    NavItem("Semestry", "/course/%s/semesters"),
    NavItem("Dane", "/course/%s/data")
]


PROJECTS_NAV_ITEMS = [
    NavItem("Dane", "/projects/%s/data"),
    NavItem("Kody", "/projects/%s/codes"),
    NavItem("Raport", "/projects/%s/raport")
]


SEMESTERS_NAV_ITEMS = [
    NavItem("Terminy", "/course/%s/semester/%s/dates"),
    NavItem("Dane", "/course/%s/semester/%s/data"),
    NavItem("Uczestnicy", "/course/%s/semester/%s/attendees")
]


PERSON_NAV_ITEMS = [
    NavItem("Dane", "/person/%s/data"),
    NavItem("Rodzina", "/person/%s/family"),
    NavItem("Role", "/person/%s/roles"),
    NavItem("Kursy Językowe", "/person/%s/courses"),
    NavItem("Aktywności", "/person/%s/activities"),
    NavItem("Zgody", "/person/%s/consents"),
    NavItem("Wydarzenia", "/person/%s/events")
]


def logoutUser(request):
    logout(request)
    return redirect("/")


class HomeView(TemplateView):
    template_name = "home.html"

    def get(self, request):
        context = {'request': request}
        return render(request, self.template_name, context)

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        context = {'request': request}
        try:
            user = User.objects.get(username=username)
        except:
            messages.error(request, 'Użytkownik nie istnieje')
            return render(request, self.template_name, context)
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
        else:
            messages.error(request, 'Niepoprawne hasło')
            return render(request, self.template_name, context)
        return redirect("/browse/people")


class BrowseView(TemplateView, NavigationBar):
    template_name = "browse/people.html"
    model: Model = ...
    nav_bars = [BROWSE_NAV_ITEMS]
    header_cells: list[HeaderCell] = ...
    active_nav_items: list[str] = ...
    filter_form: ModelForm = None

    def _get_fields(self, objects):
        ...

    def _get_buttons(self):
        ...

    def _get_objects(self, query):
        ...

    def get(self, request):
        filters = self.filter_form(initial={k: v for k, v in request.GET.dict().items() if k != 'q'}) if self.filter_form is not None else None
        objects = self._get_objects(request.GET.dict())
        q = request.GET.get('q') if request.GET.get('q') is not None else ''
        self._activate_nav_item()
        fields = self._get_fields(objects)
        buttons = self._get_buttons()
        table = HTMLTable(header_cells=self.header_cells, rows=fields, body_name='tbody')
        context = {'objects': objects, 'nav_bars': self.nav_bars, 'tables': [table], 'buttons': buttons, 'q': q, 'filters': filters}
        return render(request, self.template_name, context)

    def post(self, request):
        if request.POST.get('actionType') == "bulkDelete":
            ids = request.POST.get('ids').split(',')
            print(ids)
            # self.model.objects.filter(id__in=ids).delete()
        return self.get(request)


class ConcreteBrowseView(TemplateView, NavigationBar):
    template_name = "browse/people.html"
    model: Model = ...
    sec_model: Model = ...
    header_cells: list[HeaderCell] = ...
    active_nav_items: list[str] = ...
    first_setable_bar = 1
    filter_form: ModelForm = None

    def _get_fields(self, objects, **kwargs):
        ...

    def _get_buttons(self, **kwargs):
        ...

    def _get_objects(self, instances, query, **kwargs):
        ...

    def _get_instances(self, **kwargs):
        ...

    def _get_MtM_instances(self, ids, **kwargs):
        ...

    def _get_tables(self, instances, query, **kwargs):
        objects = self._get_objects(instances[-1], query=query, **kwargs)
        fields = self._get_fields(objects, **kwargs)
        return [HTMLTable(header_cells=self.header_cells, rows=fields, body_name="tbody")]

    def get(self, request, **kwargs):
        query = {k: v[0] if len(v) == 1 else v for k, v in dict(request.GET.lists()).items()}
        q = request.GET.get('q') if request.GET.get('q') is not None else ''
        instances = self._get_instances(**kwargs)
        self._activate_nav_item()
        buttons = self._get_buttons(**kwargs)
        nav_bars = self._set_nav_bars(instances, self.first_setable_bar, **kwargs)
        tables = self._get_tables(instances=instances, query=query, **kwargs)
        filters = self.filter_form(initial=query) if self.filter_form is not None else None
        context = {'nav_bars': nav_bars, 'buttons': buttons, 'tables': tables, 'q': q, 'filters': filters}
        return render(request, self.template_name, context)

    def post(self, request, **kwargs):
        if request.POST.get('actionType') == "bulkDelete":
            ids = request.POST.get('ids').split(',')
            self._get_MtM_instances(ids, **kwargs).delete()
        return self.get(request, **kwargs)


class BrowsePeopleView(BrowseView):
    model = People
    active_nav_items = ["Osoby"]
    header_cells = [
        HeaderCell("Imię i Nazwisko", 0, "th0", True),
        HeaderCell("Telefon", 1, "th1", True),
        HeaderCell("Mail", 2, "th2", True),
        HeaderCell("Kraj pochodzenia", 3, "th3", True),
        HeaderCell("Opcje", None, None, False)
    ]
    filter_form = PeopleFilter

    def _get_fields(self, objects):
        return [HTMLRow(
            [
                DataCell('data', o),
                DataCell('data', o.phone_nr),
                DataCell('data', o.mail),
                DataCell('data', o.country_code),
                DataCell('link', [Link("Zobacz", "btn btn-info btn-sm", f"/person/{o.id}/data"),
                                  Link("Usuń", "btn btn-danger btn-sm", f"/person/{o.id}/delete")])
                ], onclick=f"/person/{o.id}/data", id=o.id
        ) for o in objects]

    def _get_buttons(self):
        return [Button("Dodaj osobę", "/add/person"), Button("Importuj", "/import/people")]

    def _get_objects(self, query):
        q = query.pop('q') if 'q' in query else ''
        kwargs = format_filter_query(query)
        if 'gender__icontains' in kwargs.keys():
            kwargs['gender'] = kwargs.pop('gender__icontains')
        return self.model.objects.annotate(full_name=Concat('name', Value(' '), 'surname', Value(' '), 'pcode', output_field=CharField())).filter(
            (Q(mail__isnull=True) & (Q(full_name=q) |
                                     Q(phone_nr__icontains=q) |
                                     Q(country_code__icontains=q) |
                                     Q(is_adult__icontains=q) |
                                     Q(gender__name__icontains=q) |
                                     Q(description__icontains=q) |
                                     Q(notes__icontains=q))) |
            Q(full_name__icontains=q) |
            Q(phone_nr__icontains=q) |
            Q(country_code__icontains=q) |
            Q(is_adult__icontains=q) |
            Q(gender__name__icontains=q) |
            (Q(mail__isnull=False) & Q(mail__icontains=q)) |
            Q(description__icontains=q) |
            Q(notes__icontains=q), **kwargs
            )


class BrowseFamiliesView(BrowseView):
    model = ViewFamilies
    active_nav_items = ["Rodziny"]
    header_cells = [
        HeaderCell("Rodzic", 0, "th0", True),
        HeaderCell("Dziecko", 1, "th1", True),
        HeaderCell("Opcje", None, None, False)
    ]
    filter_form = FamilyFilter

    def _get_fields(self, objects):
        return [HTMLRow([
                DataCell('data', o.pid_parent),
                DataCell('data', o.pid_child),
                DataCell('link', [Link("Usuń", "btn btn-danger btn-sm", f"/person/{o.pid_parent.id}/family/{o.pid_child.id}/delete")])
                ]) for o in objects]

    def _get_buttons(self):
        return [Button("Dodaj rodzinę", "/add/family")]

    def _get_objects(self, query):
        q = query.pop('q') if 'q' in query else ''
        kwargs = format_filter_query(query)
        return self.model.objects.annotate(
            parent_full_name=Concat('pid_parent__name', Value(' '), 'pid_parent__surname', Value(' '), 'pid_parent__pcode', output_field=CharField()),
            child_full_name=Concat('pid_child__name', Value(' '), 'pid_child__surname', Value(' '), 'pid_child__pcode', output_field=CharField())
            ).filter(
            Q(parent_full_name__icontains=q) |
            Q(child_full_name__icontains=q), **kwargs
            )


class BrowseRolesView(BrowseView):
    model = Roles
    active_nav_items = ["Role"]
    header_cells = [
        HeaderCell("Nazwa roli", 0, "th0", True),
        HeaderCell("Opcje", None, None, False)
    ]

    def _get_fields(self, objects):
        return [HTMLRow([
                DataCell('data', o.role_name),
                DataCell('link', [Link("Zobacz", "btn btn-info btn-sm", f"/roles/{o.id}/data"),
                                  Link("Zmień nazwę", "btn btn-primary btn-sm", f"/roles/{o.id}/rename"),
                                  Link("Usuń", "btn btn-danger btn-sm", f"/roles/{o.id}/delete")])
                ], onclick=f"/roles/{o.id}/data", id=o.id) for o in objects]

    def _get_buttons(self):
        return [Button("Dodaj rolę", "/add/role"), Button("Importuj", "/import/roles")]

    def _get_objects(self, query):
        q = query.pop('q') if 'q' in query else ''
        return self.model.objects.filter(role_name__icontains=q)


class BrowseActivitiesView(BrowseView):
    model = Activities
    nav_bars = [BROWSE_NAV_ITEMS, ACTIVITIES_NAV_ITEMS]
    active_nav_items = ["Aktywności", "Przeglądaj"]
    header_cells = [
        HeaderCell("Rodzaj aktywności", 0, "th0", True),
        HeaderCell("Osoba", 1, "th1", True),
        HeaderCell("Data", 2, "th2", True),
        HeaderCell("Opcje", None, None, False)
    ]
    filter_form = ActivityFilter

    def _get_fields(self, objects):
        return [HTMLRow([
                DataCell('data', o.activity_type_id.name),
                DataCell('data', o.person_id),
                DataCell('datetime', o.date),
                DataCell('link', [Link("Zobacz", "btn btn-info btn-sm", f"/person/{o.person_id.id}/activity_type/{o.activity_type_id.id}/activity/{o.activity_id}/data"),
                                  Link("Usuń", "btn btn-danger btn-sm", f"/person/{o.person_id.id}/activity_type/{o.activity_type_id.id}/activity/{o.activity_id}/delete")])
                ], onclick=f"/person/{o.person_id.id}/activity_type/{o.activity_type_id.id}/activity/{o.activity_id}/data", id=o.id) for o in objects]

    def _get_buttons(self):
        return [Button("Dodaj aktywność", "/add_activity")]

    def _get_objects(self, query):
        q = query.pop('q') if 'q' in query else ''
        kwargs = format_filter_query(query)
        return self.model.objects.annotate(full_name=Concat('person_id__name', Value(' '), 'person_id__surname', Value(' '), 'person_id__pcode', output_field=CharField())).filter(
            Q(activity_type_id__name__icontains=q) |
            Q(full_name__icontains=q) |
            Q(date__icontains=q) |
            Q(notes__icontains=q) |
            Q(course_id__name__icontains=q) |
            Q(semester_id__name__icontains=q), **kwargs
            )


class BrowseActivityTypesView(BrowseView):
    model = ActivityTypes
    active_nav_items = ["Aktywności", "Rodzaje aktywności"]
    nav_bars = [BROWSE_NAV_ITEMS, ACTIVITIES_NAV_ITEMS]
    header_cells = [
        HeaderCell("Nazwa", 0, "th0", True),
        HeaderCell("Opcje", None, None, False)
    ]

    def _get_fields(self, objects):
        return [HTMLRow([
                DataCell('data', o.name),
                DataCell('link', [Link("Zmień nazwę", "btn btn-info btn-sm", f"/activity_type/{o.id}/rename"),
                                  Link("Usuń", "btn btn-danger btn-sm", f"/activity_type/{o.id}/delete")])
                ], id=o.id) for o in objects]

    def _get_buttons(self):
        return [Button("Dodaj rodzaj aktywności", "/add/activity_type")]

    def _get_objects(self, query):
        q = query.pop('q') if 'q' in query else ''
        return self.model.objects.filter(name__icontains=q)


class BrowseCoursesView(BrowseView):
    model = Courses
    active_nav_items = ["Kursy Językowe"]
    header_cells = [
        HeaderCell("Nazwa", 0, "th0", True),
        HeaderCell("Opis", None, None, False),
        HeaderCell("Opcje", None, None, False)
    ]
    filter_form = CourseFilter

    def _get_fields(self, objects):
        return [HTMLRow([
                DataCell('data', o),
                DataCell('data', o.description),
                DataCell('link', [Link("Zobacz", "btn btn-info btn-sm", f"/course/{o.id}/semesters"),
                                  Link("Usuń", "btn btn-danger btn-sm", f"/course/{o.id}/delete")])
                ], onclick=f"/course/{o.id}/semesters", id=o.id) for o in objects]

    def _get_buttons(self):
        return [Button("Dodaj kurs", "/add/course"),
                Button("Importuj kursy", "/import/courses"),
                Button("Importuj kursy i semestry", "/import/semesters"),
                Button("Importuj zapisane osoby", "/import/people_semesters")]

    def _get_objects(self, query):
        q = query.pop('q') if 'q' in query else ''
        kwargs = format_filter_query(query)
        return self.model.objects.filter(Q(name__icontains=q), **kwargs)


class BrowseProjectsView(BrowseView):
    model = Projects
    active_nav_items = ["Projekty"]
    header_cells = [
        HeaderCell("Nazwa", 0, "th0", True),
        HeaderCell("Opcje", None, None, False)
    ]

    def _get_fields(self, objects):
        return [HTMLRow([
                DataCell('data', o.name),
                DataCell('link', [Link("Zobacz", "btn btn-info btn-sm", f"/projects/{o.id}/data"),
                                  Link("Usuń", "btn btn-danger btn-sm", f"/projects/{o.id}/delete")])
                ], onclick=f"/projects/{o.id}/data", id=o.id) for o in objects]

    def _get_buttons(self):
        return [Button("Dodaj projekt", "/add/project")]
        # return [Button("Dodaj projekt", "addproject")]

    def _get_objects(self, query):
        q = query.pop('q') if 'q' in query else ''
        kwargs = format_filter_query(query)
        return self.model.objects.filter(Q(name__icontains=q) | Q(description__icontains=q), **kwargs)


class BrowseEventsView(BrowseView):
    model = Events
    active_nav_items = ["Wydarzenia", "Przeglądaj"]
    nav_bars = [BROWSE_NAV_ITEMS, EVENT_NAV_ITEMS]
    header_cells = [
        HeaderCell("Nazwa", 0, "th0", True),
        HeaderCell("Data", 1, "th1", True),
        HeaderCell("Opcje", None, None, False)
    ]
    filter_form = EventFilter

    def _get_fields(self, objects):
        return [HTMLRow([
                DataCell('data', o.name),
                DataCell('datetime', o.date),
                DataCell('link', [Link("Zobacz", "btn btn-info btn-sm", f"/events/{o.id}/data"),
                                  Link("Usuń", "btn btn-danger btn-sm", f"/events/{o.id}/delete")])
                ], onclick=f"/events/{o.id}/data", id=o.id) for o in objects]

    def _get_buttons(self):
        return [Button("Dodaj wydarzenie", "/add/event")]

    def _get_objects(self, query):
        q = query.pop('q') if 'q' in query else ''
        kwargs = format_filter_query(query)
        return self.model.objects.filter(
            Q(name__icontains=q) |
            Q(date__icontains=q) |
            Q(description__icontains=q) |
            Q(id_event_type__name__icontains=q), **kwargs
            )


class BrowseEventTypesView(BrowseEventsView):
    model = EventTypes
    active_nav_items = ["Wydarzenia", "Rodzaje wydarzeń"]
    header_cells = [
        HeaderCell("Nazwa", 0, "th0", True),
        HeaderCell("Opcje", None, None, False)
    ]
    filter_form = None

    def _get_fields(self, objects):
        return [HTMLRow([
                DataCell('data', o.name),
                DataCell('link', [Link("Usuń", "btn btn-danger btn-sm", f"/event_types/{o.id}/delete")])
                ], id=o.id) for o in objects]

    def _get_buttons(self):
        return [Button("Dodaj rodzaj wydarzenia", "/add/event_type")]

    def _get_objects(self, query):
        q = query.pop('q') if 'q' in query else ''
        return self.model.objects.filter(name__icontains=q)


class BrowseCategoriesView(BrowseEventsView):
    template_name = "browse/categories.html"
    model = Categories
    active_nav_items = ["Wydarzenia", "Grupy uczestników"]
    header_cells = [
        HeaderCell("Nazwa", 0, "th0", True),
        HeaderCell("Data", 1, "th1", True),
        HeaderCell("Opcje", None, None, False)
    ]

    def _get_fields(self, objects):
        return

    def _get_buttons(self):
        return [Button("Dodaj kategorię", "/add/category"), Button("Dodaj grupę", "/add/group")]

    def _get_objects(self, q):
        return self.model.objects.all()


class DeleteView(TemplateView):
    template_name = "delete.html"
    model: Model = ...

    def get(self, request, **kwargs):
        objects = self.model.objects.get(id=kwargs['fpk'])
        context = {'obj': objects}
        return render(request, self.template_name, context)

    def post(self, request, **kwargs):
        self.model.objects.get(id=kwargs['fpk']).delete()
        return redirect(request.POST.get('referer'))


def get_delete(_model: Model):
    class ConcreteDelete(DeleteView):
        model = _model
    return ConcreteDelete


class DeleteTwoPKView(TemplateView):
    template_name = "delete_no_pid.html"

    def get(self, request, fpk, spk):
        context = {'msg': self.get_msg(fpk, spk)}
        return render(request, self.template_name, context)

    def post(self, request, fpk, spk):
        self.get_instance(fpk, spk).delete()
        return redirect(request.POST.get('referer'))

    def get_instance(self, fpk, spk) -> Model:
        ...

    def get_msg(self, fpk, spk) -> str:
        ...


class DeleteFamilyView(DeleteTwoPKView):
    def get_instance(self, fpk, spk) -> Model:
        return ViewFamilies.objects.filter(pid_parent=fpk, pid_child=spk)

    def get_msg(self, fpk, spk) -> str:
        family = ViewFamilies.objects.get(pid_parent=fpk, pid_child=spk)
        return f"Rodzina {family.pid_parent}(rodzic) i {family.pid_child}(dziecko)"


class DeleteSemesterView(DeleteTwoPKView):
    def get_instance(self, fpk, spk) -> Model:
        return Semesters.objects.filter(course_id=fpk, id=spk)

    def get_msg(self, fpk, spk) -> str:
        semester = Semesters.objects.get(course_id=fpk, id=spk)
        return f"Semestr {semester} kursu {semester.course_id}"


class DeleteAttendeesView(DeleteTwoPKView):
    def get_instance(self, fpk, spk) -> Model:
        return Attendees.objects.filter(event=fpk, group=spk)

    def get_msg(self, fpk, spk) -> str:
        attendees = Attendees.objects.get(event=fpk, group=spk)
        return f"Uczestnicy \"{attendees.event}\" z grupy \"{attendees.group}\" w liczbie \"{attendees.no_attendees}\""


class DeletePeopleRolesView(DeleteTwoPKView):
    def get_instance(self, fpk, spk) -> Model:
        return PeopleRoles.objects.filter(pid=fpk, rid=spk)

    def get_msg(self, fpk, spk) -> str:
        plp_with_roles = PeopleRoles.objects.get(pid=fpk, rid=spk)
        return f"Rola \"{plp_with_roles.rid}\" u osoby \"{plp_with_roles.pid}\""


class DeleteRolesActivityTypesView(DeleteTwoPKView):
    def get_instance(self, fpk, spk) -> Model:
        return RolesActivityTypes.objects.filter(rid=fpk, atid=spk)

    def get_msg(self, fpk, spk) -> str:
        roles_activity_types = RolesActivityTypes.objects.get(rid=fpk, atid=spk)
        return f"Dozwolony rodzaj aktywności \"{roles_activity_types.atid}\" dla roli \"{roles_activity_types.rid}\""


class DeleteCodesView(DeleteTwoPKView):
    def get_instance(self, fpk, spk) -> Model:
        return Codes.objects.filter(project_id=fpk, cid=spk)

    def get_msg(self, fpk, spk) -> str:
        code = Codes.objects.get(project_id=fpk, cid=spk)
        return f"Kod \"{code}\" w projekcie \"{code.project_id}\""


class DeleteActivityView(DeleteTwoPKView):
    template_name = "delete_no_pid.html"

    def get(self, request, fpk, spk, tpk):
        activity = Activities.objects.get(person_id=fpk, activity_type_id=spk, activity_id=tpk)
        context = {'msg': f"Aktywność {activity.activity_type_id} u osoby {activity.person_id}"}
        return render(request, self.template_name, context)

    def post(self, request, fpk, spk, tpk):
        Activities.objects.filter(person_id=fpk, activity_type_id=spk, activity_id=tpk).delete()
        return redirect(request.POST.get('referer'))


class DeleteConsentView(DeleteTwoPKView):
    template_name = "delete_no_pid.html"

    def get(self, request, fpk, spk):
        consent = Consents.objects.get(person_id=fpk, consent_id=spk)
        context = {'msg': f"Zgoda {consent.person_id}"}
        return render(request, self.template_name, context)

    def post(self, request, fpk, spk):
        Consents.objects.filter(person_id=fpk, consent_id=spk).delete()
        return redirect(request.POST.get('referer'))


class DeletePeopleEventsView(DeleteTwoPKView):
    template_name = "delete_no_pid.html"

    def get(self, request, fpk, spk):
        plp_event = PeopleEvents.objects.get(event_id=fpk, person_id=spk)
        context = {'msg': f"Uczestnictwo {plp_event.person_id} w {plp_event.event_id}"}
        return render(request, self.template_name, context)

    def post(self, request, fpk, spk):
        PeopleEvents.objects.filter(event_id=fpk, person_id=spk).delete()
        return redirect(request.POST.get('referer'))


class AddView(TemplateView, NavigationBar):
    template_name = "add_from_form.html"
    title: str = ...
    form: ModelForm = ...
    first_setable_bar: int = 1

    def _override_form(self, context: dict, form: ModelForm = None):
        if form is not None:
            context['form'] = form

    def _expand_context(self, context):
        return context

    def get(self, request, form: ModelForm = None):
        self._activate_nav_item()
        nav_bars = self._set_nav_bars([], self.first_setable_bar)
        context = {'form': self.form, 'title': self.title, 'nav_bars': nav_bars}
        context = self._expand_context(context)
        self._override_form(context, form)
        return render(request, self.template_name, context)

    def post(self, request):
        form = self.form(data=request.POST)
        if form.is_valid():
            form.save()
            return redirect(request.POST.get('referer'))
        else:
            request.META['HTTP_REFERER'] = request.POST['referer']
            return self.get(request, form)


def get_concrete_addView(_title: str, _form: ModelForm, _nav_bars: list[NavItem], _active_nav_items: list[str], _first_setable_bar: int = 1) -> AddView:
    class ConcreteAddView(AddView):
        title = _title
        form = _form
        nav_bars = _nav_bars
        active_nav_items = _active_nav_items
        first_setable_bar = _first_setable_bar
    return ConcreteAddView


class AddActivityView(AddView):
    title = "Dodaj aktywność"
    form = ActivitiesForm
    nav_bars = [BROWSE_NAV_ITEMS, ACTIVITIES_NAV_ITEMS]
    active_nav_items = ["Aktywności", "Przeglądaj"]
    first_setable_bar = 2

    def _expand_context(self, context):
        semesters = Semesters.objects.all()
        d = {}
        for s in semesters:
            if s.course_id.id not in d.keys():
                d[s.course_id.id] = []
            d[s.course_id.id].append(s.id)
        context.update({
            'dict': d
            })
        return context

    def post(self, request):
        request.POST._mutable = True
        form = self.form(data=request.POST)
        if form.is_valid():
            if form['checkbox'].value():
                form.save()
            else:
                request.POST.update({'course_id': None, 'semester_id': None})
                self.form(data=request.POST).save()
            return redirect(request.POST.get('referer'))
        else:
            context = {'form': form, 'title': self.title}
            semesters = Semesters.objects.all()
            d = {}
            for s in semesters:
                if s.course_id.id not in d.keys():
                    d[s.course_id.id] = []
                d[s.course_id.id].append(s.id)
            context.update({
                'dict': d
                })
            return render(request, self.template_name, context=context)


class AddMulPKView(AddView):
    template_name: str = "add_from_form.html"
    initial_pks: dict[str] = ...
    title: str = ...
    form: ModelForm = ...
    model: Model = ...

    def _get_instances(self, **kwargs):
        return [self.model.objects.get(id=kwargs['fpk'])]

    def get(self, request, form: ModelForm = None, **kwargs):
        if form is None:
            form = self.form(initial={v: kwargs[k] for k, v in self.initial_pks.items()})
        form.disable(self.initial_pks.values())
        instances = self._get_instances(**kwargs)
        self._activate_nav_item()
        nav_bars = self._set_nav_bars(instances, self.first_setable_bar, **kwargs)
        context = {'form': form, 'title': self.title, 'nav_bars': nav_bars}
        context = self.expand_context(context, **kwargs)
        return render(request, self.template_name, context)

    def post(self, request, **kwargs):
        request.POST._mutable = True
        request.POST.update({v: kwargs[k] for k, v in self.initial_pks.items()})
        form = self.form(data=request.POST)
        if form.is_valid():
            form.save()
            return redirect(request.POST.get('referer'))
        else:
            request.META['HTTP_REFERER'] = request.POST['referer']
            return self.get(request, form, **kwargs)

    def expand_context(self, context, **kwargs):
        return context


def get_concrete_AddMulPKView(_initial_pks: dict[str], _title: str, _form: ModelForm, _model: Model, _nav_bars: list[NavItem], _active_nav_items: list[str], _first_setable_bar: int = 1) -> AddView:
    class ConcreteAddMulPKView(AddMulPKView):
        initial_pks = _initial_pks
        title = _title
        form = _form
        model = _model
        nav_bars = _nav_bars
        active_nav_items = _active_nav_items
        first_setable_bar = _first_setable_bar
    return ConcreteAddMulPKView


class AddSemesterDatesView(AddMulPKView):
    initial_pks = {"fpk": "course_id", "spk": "semester_id"}
    title = "Dodaj termin"
    form = SemesterDatesForm
    nav_bars = [BROWSE_NAV_ITEMS, COURSES_NAV_ITEMS, SEMESTERS_NAV_ITEMS]
    active_nav_items = ["Kursy Językowe", "Semestry", "Terminy"]

    def _get_instances(self, **kwargs):
        return [Courses.objects.get(id=kwargs['fpk']), Semesters.objects.get(course_id=kwargs['fpk'], id=kwargs['spk'])]

    def expand_context(self, context: dict, **kwargs):
        context.update({
            'object': Courses.objects.get(id=kwargs['fpk']),
            'semester': Semesters.objects.get(course_id=kwargs['fpk'], id=kwargs['spk'])
            })
        return context


class AddSemesterToPeopleSemestersView(AddMulPKView):
    initial_pks = {"fpk": "course_id", "spk": "semester_id"}
    title = "Dodaj uczestnika"
    form = PeopleSemestersForm
    nav_bars = [BROWSE_NAV_ITEMS, COURSES_NAV_ITEMS, SEMESTERS_NAV_ITEMS]
    active_nav_items = ["Kursy Językowe", "Semestry", "Uczestnicy"]

    def _get_instances(self, **kwargs):
        return [Courses.objects.get(id=kwargs['fpk']), Semesters.objects.get(course_id=kwargs['fpk'], id=kwargs['spk'])]

    def expand_context(self, context: dict, **kwargs):
        context.update({
            'object': Courses.objects.get(id=kwargs['fpk']),
            'semester': Semesters.objects.get(course_id=kwargs['fpk'], id=kwargs['spk'])
            })
        return context


class AddEventPeopleEventsView(AddMulPKView):
    initial_pks = {'fpk': "event_id"}
    title = "Dodaj osobę"
    form = EventPeopleEventsForm
    model = Events
    nav_bars = [BROWSE_NAV_ITEMS, EVENT_NAV_ITEMS, CON_EVENT_NAV_ITEMS]
    active_nav_items = ["Wydarzenia", "Przeglądaj", "Obecność"]
    first_setable_bar = 2


class AddPersonToPeopleSemestersView(AddMulPKView):
    initial_pks = {'fpk': "person_id"}
    title = "Zapisz na kurs"
    form = PeopleSemestersForm
    model = People
    nav_bars = [BROWSE_NAV_ITEMS, PERSON_NAV_ITEMS]
    active_nav_items = ["Osoby", "Kursy Językowe"]

    def expand_context(self, context: dict, **kwargs):
        semesters = Semesters.objects.all()
        d = {}
        for s in semesters:
            if s.course_id.id not in d.keys():
                d[s.course_id.id] = []
            d[s.course_id.id].append(s.id)
        context.update({
            'object': People.objects.get(id=kwargs['fpk']),
            'dict': d
            })
        return context


class AddPersonActivityView(AddMulPKView):
    initial_pks = {'fpk': "person_id"}
    title = "Dodaj aktywność"
    form = ActivitiesForm
    model = People
    nav_bars = [BROWSE_NAV_ITEMS, PERSON_NAV_ITEMS]
    active_nav_items = ["Osoby", "Aktywności"]

    def post(self, request, **kwargs):
        request.POST._mutable = True
        request.POST.update({v: kwargs[k] for k, v in self.initial_pks.items()})
        form = self.form(data=request.POST)
        if form.is_valid():
            if form['checkbox'].value():
                form.save()
            else:
                request.POST.update({'course_id': None, 'semester_id': None})
                self.form(data=request.POST).save()
            return redirect(request.POST.get('referer'))

    def expand_context(self, context: dict, **kwargs):
        semesters = Semesters.objects.all()
        d = {}
        for s in semesters:
            if s.course_id.id not in d.keys():
                d[s.course_id.id] = []
            d[s.course_id.id].append(s.id)
        context.update({
            'object': People.objects.get(id=kwargs['fpk']),
            'dict': d
            })
        return context


class AddConsentView(AddMulPKView):
    initial_pks = {'fpk': "person_id"}
    title = "Dodaj zgodę"
    form = ConsentsForm
    model = People
    nav_bars = [BROWSE_NAV_ITEMS, PERSON_NAV_ITEMS]
    active_nav_items = ["Osoby", "Zgody"]

    def expand_context(self, context: dict, **kwargs):
        context.update({
            'object': People.objects.get(id=kwargs['fpk'])
            })
        return context


class AddFamilyView(TemplateView, NavigationBar):
    template_name = "add_family.html"
    nav_bars = [BROWSE_NAV_ITEMS, PERSON_NAV_ITEMS]
    active_nav_items = ['Osoby', 'Rodzina']

    def get(self, request, fpk):
        person = People.objects.get(id=fpk)
        families = ViewFamilies.objects.filter(Q(pid_parent=fpk) | Q(pid_child=fpk)).values_list("pid_parent", "pid_child")
        families_ids = list(set([pid for x in families for pid in x]))
        people = People.objects.exclude(id__in=families_ids)
        nav_bars = self._set_nav_bars([person], fpk=fpk)
        # TODO nie można dodać osób już będących w rodzinie z person
        context = {'people': people, 'nav_bars': nav_bars}
        return render(request, self.template_name, context)

    def post(self, request, fpk):
        if request.method == 'POST':
            parent = People.objects.get(id=fpk)
            child = People.objects.get(id=request.POST.__getitem__('member'))
            if request.POST.__getitem__('relationship') == 'parent':
                parent, child = child, parent
            elif request.POST.__getitem__('relationship') == 'child':
                pass
            child.parents.add(parent)
            return redirect(f'/person/{fpk}/family')


class RoleDataView(ConcreteBrowseView):
    active_nav_items = ["Role", "Osoby z rolą"]
    header_cells = [
        HeaderCell("Osoba", 0, "th0", True),
        HeaderCell("Opcje", None, None, False)
    ]
    nav_bars = [BROWSE_NAV_ITEMS, ROLES_NAV_ITEMS]

    def _get_fields(self, objects, **kwargs):
        return [HTMLRow([
                DataCell('data', o),
                DataCell('link', [Link("Zobacz", "btn btn-info btn-sm", f"/person/{o.id}/data"),
                                  Link("Usuń", "btn btn-danger btn-sm", f"/person/{o.id}/role/{kwargs['fpk']}/delete")])
                ], onclick=f"/person/{o.id}/data", id=o.id) for o in objects]

    def _get_buttons(self, **kwargs):
        return [Button("Daj rolę osobie", f"/roles/{kwargs['fpk']}/grant_role")]

    def _get_objects(self, instance, query, **kwargs):
        q = query.pop('q') if 'q' in query else ''
        kwargs = format_filter_query(query)
        return instance.plp_w_roles.annotate(full_name=Concat('name', Value(' '), 'surname', Value(' '), 'pcode', output_field=CharField())).filter(
            Q(full_name__icontains=q), **kwargs
            )

    def _get_instances(self, **kwargs):
        return [Roles.objects.get(id=kwargs['fpk'])]

    def _get_MtM_instances(self, ids, **kwargs):
        return PeopleRoles.objects.filter(rid=kwargs['fpk'], pid__in=ids)


class RoleBrowseView(ConcreteBrowseView):
    active_nav_items = ["Role", "Dozwolone aktywności"]
    header_cells = [
        HeaderCell("Dozwolone aktywności", 0, "th0", True),
        HeaderCell("Opcje", None, None, False)
    ]
    nav_bars = [BROWSE_NAV_ITEMS, ROLES_NAV_ITEMS]

    def _get_fields(self, objects, **kwargs):
        return [HTMLRow([
                DataCell('data', o.atid.name),
                DataCell('link', [Link("Usuń", "btn btn-danger btn-sm", f"/roles/{kwargs['fpk']}/activity_type/{o.atid.id}/delete")])
                ], id=o.atid.id) for o in objects]

    def _get_buttons(self, **kwargs):
        return [Button("Dodaj dozwolony rodzaj aktywności", f"/roles/{kwargs['fpk']}/activity_type/add")]

    def _get_objects(self, instance, query, **kwargs):
        q = query.pop('q') if 'q' in query else ''
        return RolesActivityTypes.objects.filter(rid=kwargs['fpk'], atid__name__icontains=q).select_related()

    def _get_instances(self, **kwargs):
        return [Roles.objects.get(id=kwargs['fpk'])]

    def _get_MtM_instances(self, ids, **kwargs):
        return RolesActivityTypes.objects.filter(rid=kwargs['fpk'], atid__in=ids)


class PersonRolesView(ConcreteBrowseView):
    active_nav_items = ["Osoby", "Role"]
    header_cells = [
        HeaderCell("Rola", 0, "th0", True),
        HeaderCell("Opcje", None, None, False)
    ]
    nav_bars = [BROWSE_NAV_ITEMS, PERSON_NAV_ITEMS]

    def _get_fields(self, objects, **kwargs):
        return [HTMLRow([
                DataCell('data', o.role_name),
                DataCell('link', [Link("Zobacz", "btn btn-info btn-sm", f"/roles/{o.id}/data"),
                                  Link("Usuń", "btn btn-danger btn-sm", f"/person/{kwargs['fpk']}/role/{o.id}/delete")])
                ], onclick=f"/roles/{o.id}/data", id=o.id) for o in objects]

    def _get_buttons(self, **kwargs):
        return [Button("Daj rolę", f"/person/{kwargs['fpk']}/grant_role")]

    def _get_objects(self, instance, query, **kwargs):
        q = query.pop('q') if 'q' in query else ''
        return instance.roles_set.filter(role_name__icontains=q)

    def _get_instances(self, **kwargs):
        return [People.objects.get(id=kwargs['fpk'])]

    def _get_MtM_instances(self, ids, **kwargs):
        return PeopleRoles.objects.filter(pid=kwargs['fpk'], rid__in=ids)


class PersonGrantRoleView(AddMulPKView):
    initial_pks = {'fpk': "pid"}
    title = "Daj rolę"
    form = GrantRoleForm
    model = People
    nav_bars = [BROWSE_NAV_ITEMS, PERSON_NAV_ITEMS]
    active_nav_items = ["Osoby", "Role"]

    def expand_context(self, context: dict, **kwargs):
        context.update({
            'object': People.objects.get(id=kwargs['fpk'])
            })
        return context


class PersonAddToEventView(AddMulPKView):
    initial_pks = {'fpk': "person_id"}
    title = "Dodaj do wydarzenia"
    form = PersonPeopleEventsForm
    model = People
    nav_bars = [BROWSE_NAV_ITEMS, PERSON_NAV_ITEMS]
    active_nav_items = ["Osoby", "Wydarzenia"]

    def expand_context(self, context: dict, **kwargs):
        context.update({
            'object': People.objects.get(id=kwargs['fpk'])
            })
        return context


class PersonCoursesView(ConcreteBrowseView):
    active_nav_items = ["Osoby", "Kursy Językowe"]
    header_cells = [
        HeaderCell("Kurs", 0, "th0", True),
        HeaderCell("Semestr", 1, "th1", True),
        HeaderCell("Opcje", None, None, False)
    ]
    nav_bars = [BROWSE_NAV_ITEMS, PERSON_NAV_ITEMS]
    filter_form = PersonCourseFilter

    def _get_fields(self, objects, **kwargs):
        return [HTMLRow([
                DataCell('data', o.course_id),
                DataCell('data', o.semester_id),
                DataCell('link', [Link("Zobacz kurs", "btn btn-info btn-sm", f"/course/{o.course_id.id}/semester/{o.semester_id.id}/dates"),
                                  Link("Zobacz obecności", "btn btn-info btn-sm", f"/person/{kwargs['fpk']}/course/{o.course_id.id}/semester/{o.semester_id.id}/attendance"),
                                  Link("Wypisz", "btn btn-danger btn-sm", f"/course/{o.course_id.id}/semester/{o.semester_id.id}/person/{kwargs['fpk']}/delete_attendance")])
                ], onclick=f"/course/{o.course_id.id}/semester/{o.semester_id.id}/dates", id=[o.course_id.id, o.semester_id.id]) for o in objects]

    def _get_buttons(self, **kwargs):
        return [Button("Zapisz na kurs", f"/person/{kwargs['fpk']}/add_to_course")]

    def _get_objects(self, instance, query, **kwargs):
        q = query.pop('q') if 'q' in query else ''
        kw = format_filter_query(query)
        return PeopleSemesters.objects.filter(
            Q(course_id__name__icontains=q) | Q(semester_id__name__icontains=q),
            person_id=kwargs['fpk'], **kw
            ).select_related()

    def _get_instances(self, **kwargs):
        return [People.objects.get(id=kwargs['fpk'])]

    def _get_MtM_instances(self, ids, **kwargs):
        ids = [id.replace('[', '').replace(']', '') for id in ids]
        return PeopleSemesters.objects.filter(person_id=kwargs['fpk'], course_id__id__in=ids[::2], semester_id__id__in=ids[1::2])


class PersonEventsView(ConcreteBrowseView):
    active_nav_items = ["Osoby", "Wydarzenia"]
    header_cells = [
        HeaderCell("Wydarzenie", 0, "th0", True),
        HeaderCell("Obecność", 1, "th1", True),
        HeaderCell("Opcje", None, None, False)
    ]
    nav_bars = [BROWSE_NAV_ITEMS, PERSON_NAV_ITEMS]

    def _get_fields(self, objects, **kwargs):
        return [HTMLRow([
                DataCell('data', o.event_id),
                DataCell('data', o.attendance_type),
                DataCell('link', [Link("Zobacz wydarzenie", "btn btn-info btn-sm", f"/events/{o.event_id.id}/attendance"),
                                  # Link("Zobacz obecności", "btn btn-info btn-sm", f"/person/{kwargs['fpk']}/course/{o.course_id.id}/semester/{o.semester_id.id}/attendance"),
                                  Link("Wypisz", "btn btn-danger btn-sm", f"/events/{o.event_id.id}/person/{o.person_id.id}/delete_attendance")])
                ], onclick=f"/events/{o.event_id.id}/attendance", id=o.event_id.id) for o in objects]

    def _get_buttons(self, **kwargs):
        return [Button("Zapisz na wydarzenie", f"/person/{kwargs['fpk']}/add_to_event")]

    def _get_objects(self, instance, query, **kwargs):
        q = query.pop('q') if 'q' in query else ''
        return PeopleEvents.objects.filter(
            person_id=kwargs['fpk'],
            event_id__name__icontains=q
            ).select_related()

    def _get_instances(self, **kwargs):
        return [People.objects.get(id=kwargs['fpk'])]

    def _get_MtM_instances(self, ids, **kwargs):
        return PeopleEvents.objects.filter(person_id=kwargs['fpk'], event_id__in=ids)


class PersonAttendanceView(ConcreteBrowseView):
    # TODO nie działa!!!!
    active_nav_items = ["Osoby", "Kursy Językowe", ""]
    nav_bars = [BROWSE_NAV_ITEMS, PERSON_NAV_ITEMS, []]
    header_cells = [
        HeaderCell("Data", 0, "th0", True),
        HeaderCell("Od", None, None, False),
        HeaderCell("Do", None, None, False),
        HeaderCell("Obecność", 3, "th3", True)
    ]

    def _get_fields(self, objects, **kwargs):
        return [HTMLRow([
                DataCell('date', o.date_id.date),
                DataCell('time', o.date_id.start_time),
                DataCell('time', o.date_id.end_time),
                DataCell('data', o.attendance_type)
                ], id=o.date_id.id) for o in objects]

    def _get_buttons(self, **kwargs):
        return [Button("Edytuj", f"/person/{kwargs['fpk']}/course/{kwargs['spk']}/semester/{kwargs['tpk']}/attendance/edit")]

    def _get_objects(self, instance, query, **kwargs):
        q = query.pop('q') if 'q' in query else ''
        return Attendance.objects.filter(person_id=kwargs['fpk'], course_id=kwargs['spk'], semester_id=kwargs['tpk'])

    def _get_instances(self, **kwargs):
        return [People.objects.get(id=kwargs['fpk']), Courses.objects.get(id=kwargs['spk']), Semesters.objects.get(course_id=kwargs['spk'], id=kwargs['tpk'])]

    def _get_MtM_instances(self, ids, **kwargs):
        return Attendance.objects.filter(person_id=kwargs['fpk'], course_id=kwargs['spk'], semester_id=kwargs['tpk'], date_id__id__in=ids)


class PersonAttendanceEditView(TemplateView, NavigationBar):
    template_name = "person/attendance_edit.html"
    nav_bars = [BROWSE_NAV_ITEMS, PERSON_NAV_ITEMS, []]
    active_nav_items = ['Osoby', 'Kursy', '']

    def get(self, request, fpk, spk, tpk):
        person = People.objects.get(id=fpk)
        course = Courses.objects.get(id=spk)
        semester = Semesters.objects.get(course_id=spk, id=tpk)
        attendance = Attendance.objects.filter(person_id=fpk, course_id=spk, semester_id=tpk).select_related()
        forms = [EditAttendanceFromPerson(instance=att) for att in attendance]
        self._activate_nav_item()
        nav_bars = self._set_nav_bars([person, course], fpk=fpk, spk=spk, tpk=tpk)
        context = {'object': person, 'semester': semester, 'objects': forms, 'nav_bars': nav_bars}
        return render(request, self.template_name, context)

    def post(self, request, fpk, spk, tpk):
        attendance_types = request.POST.getlist('attendance_type')
        dids = request.POST.getlist('date_id')
        for did, att in zip(dids, attendance_types):
            Attendance.objects.filter(person_id=fpk, course_id=spk, semester_id=tpk, date_id=did).update(attendance_type=att)
        return redirect(request.POST.get('referer'))


class PersonActivitiesView(ConcreteBrowseView):
    active_nav_items = ["Osoby", "Aktywności"]
    header_cells = [
        HeaderCell("Rodzaj aktywności", 0, "th0", True),
        HeaderCell("Data", 1, "th1", True),
        HeaderCell("Opcje", None, None, False)
    ]
    nav_bars = [BROWSE_NAV_ITEMS, PERSON_NAV_ITEMS]
    filter_form = PersonActivitiesFilter

    def _get_fields(self, objects, **kwargs):
        return [HTMLRow([
                DataCell('data', o.activity_type_id.name),
                DataCell('datetime', o.date),
                DataCell('link', [Link("Zobacz", "btn btn-info btn-sm", f"/person/{o.person_id.id}/activity_type/{o.activity_type_id.id}/activity/{o.activity_id}/data"),
                                  Link("Usuń", "btn btn-danger btn-sm", f"/person/{o.person_id.id}/activity_type/{o.activity_type_id.id}/activity/{o.activity_id}/delete")])
                ], onclick=f"/person/{o.person_id.id}/activity_type/{o.activity_type_id.id}/activity/{o.activity_id}/data", id=[o.activity_id, o.activity_type_id.id]) for o in objects]

    def _get_buttons(self, **kwargs):
        return [Button("Dodaj aktywność", f"/person/{kwargs['fpk']}/add_activity")]

    def _get_objects(self, instance, query, **kwargs):
        q = query.pop('q') if 'q' in query else ''
        kw = format_filter_query(query)
        return Activities.objects.filter(Q(person_id=kwargs['fpk'], activity_type_id__name__icontains=q), **kw)

    def _get_instances(self, **kwargs):
        return [People.objects.get(id=kwargs['fpk'])]

    def _get_MtM_instances(self, ids, **kwargs):
        ids = [id.replace('[', '').replace(']', '') for id in ids]
        return Activities.objects.filter(person_id=kwargs['fpk'], activity_id__in=ids[::2], activity_type_id__id__in=ids[1::2])


class PersonConsentsView(ConcreteBrowseView):
    active_nav_items = ["Osoby", "Zgody"]
    header_cells = [
        HeaderCell("Powiązana aktywność", 0, "th0", True),
        HeaderCell("Opcje", None, None, False)
    ]
    nav_bars = [BROWSE_NAV_ITEMS, PERSON_NAV_ITEMS]

    def _get_fields(self, objects, **kwargs):
        return [HTMLRow([
                DataCell('data', o.activity_type_id.name),
                DataCell('link', [Link("Zobacz", "btn btn-info btn-sm", f"/person/{o.person_id.id}/consent/{o.consent_id}/data"),
                                  Link("Usuń", "btn btn-danger btn-sm", f"/person/{o.person_id.id}/consent/{o.consent_id}/delete")])
                ], onclick=f"/person/{o.person_id.id}/consent/{o.consent_id}/data", id=o.consent_id) for o in objects]

    def _get_buttons(self, **kwargs):
        return [Button("Dodaj zgodę", f"/person/{kwargs['fpk']}/add_consent")]

    def _get_objects(self, instance, query, **kwargs):
        q = query.pop('q') if 'q' in query else ''
        kw = format_filter_query(query)
        return Consents.objects.filter(person_id=kwargs['fpk'], activity_type_id__name__icontains=q)

    def _get_instances(self, **kwargs):
        return [People.objects.get(id=kwargs['fpk'])]

    def _get_MtM_instances(self, ids, **kwargs):
        return Consents.objects.filter(person_id=kwargs['fpk'], consent_id__in=ids)


class PersonFamilyView(ConcreteBrowseView):
    active_nav_items = ["Osoby", "Rodzina"]
    parents_header_cells = [
        HeaderCell("Rodzic", 0, "th0", True),
        HeaderCell("Opcje", None, None, False)
    ]
    children_header_cells = [
        HeaderCell("Dziecko", 0, "th1", True),
        HeaderCell("Opcje", None, None, False)
    ]
    nav_bars = [BROWSE_NAV_ITEMS, PERSON_NAV_ITEMS]
    filter_form = PeopleFilter

    def _get_buttons(self, **kwargs):
        return [Button("Dodaj członka rodziny", f"/person/{kwargs['fpk']}/add_family")]

    def _get_instances(self, **kwargs):
        return [People.objects.get(id=kwargs['fpk'])]

    def _get_tables(self, instances, query, **kwargs):
        q = query.pop('q') if 'q' in query else ''
        query['gender__name'] = query.pop('gender') if 'gender' in query.keys() else ""
        kwargs = format_filter_query(query)
        person = instances[0]
        parents = person.parents.annotate(full_name=Concat('name', Value(' '), 'surname', Value(' '), 'pcode', output_field=CharField())).filter(Q(full_name__icontains=q), **kwargs)
        children = person.people_set.annotate(full_name=Concat('name', Value(' '), 'surname', Value(' '), 'pcode', output_field=CharField())).filter(Q(full_name__icontains=q), **kwargs)
        p_fields = [HTMLRow([
                DataCell('data', o),
                DataCell('link', [Link("Zobacz", "btn btn-info btn-sm", f"/person/{o.id}/data"),
                                  Link("Usuń", "btn btn-danger btn-sm", f"/person/{o.id}/family/{person.id}/delete")])
                ], onclick=f"/person/{o.id}/data", id=[o.id, person.id]) for o in parents]
        c_fields = [HTMLRow([
                DataCell('data', o),
                DataCell('link', [Link("Zobacz", "btn btn-info btn-sm", f"/person/{o.id}/data"),
                                  Link("Usuń", "btn btn-danger btn-sm", f"/person/{person.id}/family/{o.id}/delete")])
                ], onclick=f"/person/{o.id}/data", id=[person.id, o.id]) for o in children]
        return [HTMLTable(header_cells=self.parents_header_cells, rows=p_fields, body_name="parents_tbody"),
                HTMLTable(header_cells=self.children_header_cells, rows=c_fields, body_name="children_tbody")]

    def _get_MtM_instances(self, ids, **kwargs):
        ids = [id.replace('[', '').replace(']', '') for id in ids]
        return ViewFamilies.objects.filter(pid_parent__in=ids[::2], pid_child__in=ids[1::2])


class CoursesSemestersView(ConcreteBrowseView):
    active_nav_items = ["Kursy Językowe", "Semestry"]
    nav_bars = [BROWSE_NAV_ITEMS, COURSES_NAV_ITEMS]
    header_cells = [
        HeaderCell("Semestr", 0, "th0", True),
        HeaderCell("Opis", 1, "th1", True),
        HeaderCell("Opcje", None, None, False)
    ]
    filter_form = CourseSemesterFilter

    def _get_fields(self, objects, **kwargs):
        return [HTMLRow([
                DataCell('data', o.name),
                DataCell('data', o.description),
                DataCell('link', [Link("Zobacz", "btn btn-info btn-sm", f"/course/{kwargs['fpk']}/semester/{o.id}/dates"),
                                  Link("Usuń", "btn btn-danger btn-sm", f"/course/{kwargs['fpk']}/semester/{o.id}/delete")])
                ], onclick=f"/course/{kwargs['fpk']}/semester/{o.id}/dates", id=o.id) for o in objects]

    def _get_buttons(self, **kwargs):
        return [Button("Dodaj semestr", f"/course/{kwargs['fpk']}/add/semester")]

    def _get_objects(self, instance, query, **kwargs):
        q = query.pop('q') if 'q' in query else ''
        kw = format_filter_query(query)
        return Semesters.objects.filter(Q(course_id=kwargs['fpk'], name__icontains=q), **kw)

    def _get_instances(self, **kwargs):
        return [Courses.objects.get(id=kwargs['fpk'])]

    def _get_MtM_instances(self, ids, **kwargs):
        return Semesters.objects.filter(course_id=kwargs['fpk'], id__in=ids)


class DataView(TemplateView, NavigationBar):
    template_name: str = ...
    model: Model = ...
    form: ModelForm = ...
    edit_href: str = ...
    first_setable_bar: int = 1

    def get(self, request, **kwargs):
        instances = self._get_instances(**kwargs)
        form = self.form(instance=instances[-1])
        form.disable(["__all"])
        self._activate_nav_item()
        nav_bars = self._set_nav_bars(instances, self.first_setable_bar, **kwargs)
        edit_button = Button("Edytuj", self.edit_href % tuple([item for _, item in kwargs.items()]))
        context = {'form': form, 'nav_bars': nav_bars, 'edit_button': edit_button}
        return render(request, self.template_name, context)

    def _get_instances(self, **kwargs):
        return [self.model.objects.get(id=kwargs['fpk'])]


class SemestersDataView(DataView):
    template_name = "person/data.html"
    model = Semesters
    form = SemesterForm
    active_nav_items = ["Kursy Językowe", "Semestry", "Dane"]
    nav_bars = [BROWSE_NAV_ITEMS, COURSES_NAV_ITEMS, SEMESTERS_NAV_ITEMS]
    edit_href = "/course/%s/semester/%s/data/edit"

    def _get_instances(self, **kwargs):
        return [Courses.objects.get(id=kwargs['fpk']), self.model.objects.get(course_id=kwargs['fpk'], id=kwargs['spk'])]


class EventsDataView(DataView):
    template_name = "person/data.html"
    model = Events
    form = EventForm
    active_nav_items = ["Wydarzenia", "Przeglądaj", "Dane"]
    nav_bars = [BROWSE_NAV_ITEMS, EVENT_NAV_ITEMS, CON_EVENT_NAV_ITEMS]
    edit_href = "/events/%s/data/edit"
    first_setable_bar = 2


class CourseView(DataView):
    template_name = "person/data.html"
    model = Courses
    form = CoursesForm
    active_nav_items = ["Kursy Językowe", "Dane"]
    nav_bars = [BROWSE_NAV_ITEMS, COURSES_NAV_ITEMS]
    edit_href = "/course/%s/data/edit"


class ProjectDataView(DataView):
    template_name = "person/data.html"
    model = Projects
    form = ProjectForm
    active_nav_items = ["Projekty", "Dane"]
    nav_bars = [BROWSE_NAV_ITEMS, PROJECTS_NAV_ITEMS]
    edit_href = "/projects/%s/data/edit"


class PersonDataView(DataView):
    template_name = "person/data.html"
    model = People
    form = PersonForm
    active_nav_items = ["Osoby", "Dane"]
    nav_bars = [BROWSE_NAV_ITEMS, PERSON_NAV_ITEMS]
    edit_href = "/person/%s/data/edit"


class EditDataView(TemplateView, NavigationBar):
    template_name = "add_from_form.html"
    extend_file: str = ...
    model: Model = ...
    form: ModelForm = ...
    first_setable_bar = 1

    def get(self, request, **kwargs):
        instance = self.model.objects.get(id=kwargs['fpk'])
        form = self.form(instance=instance)
        self._activate_nav_item()
        nav_bars = self._set_nav_bars([instance], self.first_setable_bar, **kwargs)
        context = {'form': form, 'nav_bars': nav_bars}
        return render(request, self.template_name, context)

    def post(self, request, **kwargs):
        instance = self.model.objects.get(id=kwargs['fpk'])
        form = self.form(data=request.POST, instance=instance)
        if form.is_valid():
            form.save()
            return redirect(request.POST.get('referer'))
        else:
            return render(request, self.template_name, {'form': form})


def get_concrete_EditDataView(_extend_file: str, _model: Model, _form: ModelForm, _active_nav_items: list[str], _nav_bars: list[NavItem], _first_setable_bar: int = 1) -> EditDataView:
    class ConcreteEditDataView(EditDataView):
        extend_file = _extend_file
        model = _model
        form = _form
        active_nav_items = _active_nav_items
        nav_bars = _nav_bars
        first_setable_bar = _first_setable_bar
    return ConcreteEditDataView


class EditDataTwoPKView(TemplateView):
    template_name = "add_from_form.html"
    extend_file: str = ...
    form: ModelForm = ...

    def get(self, request, fpk, spk):
        instance = self.get_instance(fpk, spk)
        form = self.form(instance=instance)
        context = {'object': instance, 'form': form, "extend_file": self.extend_file}
        return render(request, self.template_name, context)

    def post(self, request, fpk, spk):
        ...

    def get_instance(self, fpk, spk):
        ...


class ChangeNoAttendeesView(EditDataTwoPKView):
    extend_file = "browse/main.html"
    form = AttendeesFormEdit

    def get_instance(self, fpk, spk):
        return Attendees.objects.get(event_id=fpk, group_id=spk)

    def post(self, request, fpk, spk):
        Attendees.objects.filter(event=fpk, group=spk).update(no_attendees=request.POST.__getitem__('no_attendees'))
        return redirect(request.POST.get('referer'))


class ImportView(TemplateView, NavigationBar):
    template_name = "import.html"
    desc = "Jak ma wyglądać plik: ..."
    nav_bars = [BROWSE_NAV_ITEMS]
    example_table: HTMLTable = ...

    def get(self, request):
        form = UploadFileForm()
        self._activate_nav_item()
        nav_bars = self._set_nav_bars([])
        context = {'desc': self.desc, 'form': form, 'nav_bars': nav_bars, 'tables': [self.example_table]}
        return render(request, self.template_name, context)

    def post(self, request):
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            data = read_input(request.FILES["file"])
            self.save_data(data)
            return redirect(request.POST.get('referer'))

    def save_data(self, data: dict): ...


class ImportPersonView(ImportView):
    desc = "Rozszerzenie: .csv"
    active_nav_items = ["Osoby"]
    example_table = HTMLTable(
        header_cells=[HeaderCell("lp"), HeaderCell("imie"), HeaderCell("nazwisko"), HeaderCell("telefon"), HeaderCell("mail"), HeaderCell("płeć"), HeaderCell("kraj"), HeaderCell("cecha charakterystyczna"), HeaderCell("opis")],
        rows=[
            HTMLRow([DataCell('', '1'), DataCell('', 'Jan'), DataCell('', 'Kowalski'), DataCell('', '123 456 789'), DataCell('', 'jankow@ee.ee'), DataCell('', 'mężczyzna'), DataCell('', 'Ukraina'), DataCell('', ''), DataCell('', '')]),
            HTMLRow([DataCell('', '2'), DataCell('', 'Janina'), DataCell('', 'Kowalska'), DataCell('', ''), DataCell('', 'janinkow@ee.ee'), DataCell('', ''), DataCell('', ''), DataCell('', ''), DataCell('', '')])]
    )

    def save_data(self, data):
        People.objects.bulk_create(
            [People(
                name=row['imie'],
                surname=row['nazwisko'],
                phone_nr=row['telefon'],
                mail=row['mail'],
                is_adult=map_is_adult(row['czy_pelnoletni']),
                gender=Genders.objects.get(name=row['plec']) if row['plec'] != '' else None,
                country_code=row['kraj'],
                description=row['cecha charakterystyczna'],
                notes=row['opis'],
                    ) for row in data],
            ignore_conflicts=True
        )


class ImportRoleView(ImportView):
    desc = "Rozszerzenie: .csv"
    active_nav_items = ["Role"]
    example_table = HTMLTable(
        header_cells=[HeaderCell("lp"), HeaderCell("nazwa")],
        rows=[
            HTMLRow([DataCell('', '1'), DataCell('', 'Beneficjent')]),
            HTMLRow([DataCell('', '2'), DataCell('', 'Pracownik')])]
    )

    def save_data(self, data):
        Roles.objects.bulk_create(
            [Roles(role_name=row['nazwa']) for row in data],
            ignore_conflicts=True
        )


class ImportCourseView(ImportView):
    desc = """Rozszerzenie: .csv
    Nauczyciel musi znajdować się w systemie w momencie importu
    """
    active_nav_items = ["Kursy Językowe"]
    example_table = HTMLTable(
        header_cells=[HeaderCell("lp"), HeaderCell("nazwa"), HeaderCell("opis"), HeaderCell("nauczyciel")],
        rows=[
            HTMLRow([DataCell('', '1'), DataCell('', 'Polski A1'), DataCell('', ''), DataCell('', 'Jan Kowalski')]),
            HTMLRow([DataCell('', '2'), DataCell('', 'Polski A2'), DataCell('', 'dla słowiańskojęzycznych'), DataCell('', 'Jak Kowalski 1')])]
    )

    def save_data(self, data):
        courses_list = []
        for row in data:
            name, surname, pcode = row['nauczyciel'].split(' ')
            courses_list.append(Courses(name=row['nazwa'],
                                        description=row['opis'],
                                        teacher_id=People.objects.get(name=name, surname=surname, pcode__icontains=pcode)))
        Courses.objects.bulk_create(courses_list, ignore_conflicts=True)


class ImportPeopleSemestersView(ImportView):
    desc = """Rozszerzenie: .csv
    Kursy oraz semestry muszą znajdować się w systemie w momencie importu
    """
    active_nav_items = ["Kursy Językowe"]
    example_table = HTMLTable(
        header_cells=[HeaderCell("nazwa kursu"), HeaderCell("nazwa semestru"), HeaderCell("imie"), HeaderCell("nazwisko"), HeaderCell("telefon"), HeaderCell("mail"), HeaderCell("płeć"), HeaderCell("kraj"), HeaderCell("cecha charakterystyczna"), HeaderCell("opis")],
        rows=[
            HTMLRow([DataCell('', 'Polski A1'), DataCell('', '2024Z'), DataCell('', 'Jan'), DataCell('', 'Kowalski'), DataCell('', '123 456 789'), DataCell('', 'jankow@ee.ee'), DataCell('', 'mężczyzna'), DataCell('', 'Ukraina'), DataCell('', ''), DataCell('', '')]),
            HTMLRow([DataCell('', 'Polski A1'), DataCell('', '2024L'), DataCell('', 'Jan'), DataCell('', 'Kowalski'), DataCell('', '123 456 789'), DataCell('', 'jankow@ee.ee'), DataCell('', 'mężczyzna'), DataCell('', 'Ukraina'), DataCell('', ''), DataCell('', '')]),
            HTMLRow([DataCell('', 'Polski A1'), DataCell('', '2024Z'), DataCell('', 'Janina'), DataCell('', 'Kowalska'), DataCell('', ''), DataCell('', 'janinkow@ee.ee'), DataCell('', ''), DataCell('', ''), DataCell('', ''), DataCell('', '')]),
            HTMLRow([DataCell('', 'Polski A2'), DataCell('', '2024Z'), DataCell('', 'Janina'), DataCell('', 'Kowalska'), DataCell('', ''), DataCell('', 'janinkow@ee.ee'), DataCell('', ''), DataCell('', ''), DataCell('', ''), DataCell('', '')])]
    )

    def save_data(self, data):
        people_semesters_list = []
        people_list = []
        for row in data:
            try:
                if row['mail'] == '':
                    raise People.DoesNotExist  # when mail is empty assume that person does not exist
                person = People.objects.get(mail=row['mail'])
            except People.DoesNotExist:
                people_list.append(
                    People(
                        name=row['imie'],
                        surname=row['nazwisko'],
                        phone_nr=row['telefon'],
                        mail=row['mail'],
                        is_adult=map_is_adult(row['czy_pelnoletni']),
                        gender=Genders.objects.get(name=row['plec']) if row['plec'] != '' else None,
                        country_code=row['kraj'],
                        description=row['cecha charakterystyczna'],
                        notes=row['opis']
                    )
                )
        People.objects.bulk_create(people_list, ignore_conflicts=True)
        for row in data:
            person = People.objects.get(mail=row['mail'])
            semester = Semesters.objects.get(course_id__name=row['nazwa kursu'], name=row['nazwa semestru'])
            course_id = Courses.objects.get(name=row['nazwa kursu'])
            try:
                people_semesters = PeopleSemesters.objects.get(person_id=person, semester_id=semester, course_id=course_id)
            except Courses.DoesNotExist:
                ...
            except Semesters.DoesNotExist:
                ...
            except PeopleSemesters.DoesNotExist:
                people_semesters_list.append(PeopleSemesters(
                    course_id=course_id,
                    semester_id=semester,
                    person_id=person)
                )
        PeopleSemesters.objects.bulk_create(people_semesters_list, ignore_conflicts=True)


class ImportSemestersView(ImportView):
    desc = "Rozszerzenie: .csv"
    active_nav_items = ["Kursy Językowe"]
    example_table = HTMLTable(
        header_cells=[HeaderCell("nazwa kursu"), HeaderCell("opis kursu"), HeaderCell("nazwa semestru"), HeaderCell("mail nauczyciela")],
        rows=[
            HTMLRow([DataCell('', 'Polski A1'), DataCell('', ''), DataCell('', '2024Z'), DataCell('', 'jankow@ee.ee')]),
            HTMLRow([DataCell('', 'Polski A1'), DataCell('', ''), DataCell('', '2024L'), DataCell('', 'jankow@ee.ee')]),
            HTMLRow([DataCell('', 'Polski A2'), DataCell('', 'dla słowiańskojęzycznych'), DataCell('', '2024Z'), DataCell('', 'janinkow@ee.ee')])]
    )

    def save_data(self, data):
        courses_list = []
        courses_names = []
        for row in data:
            try:
                course = Courses.objects.get(name=row["Nazwa"])
            except Courses.DoesNotExist:
                if row["Nazwa"] in courses_names:
                    continue
                try:
                    teacher = People.objects.get(mail=row["Email_nauczyciela"]) if row["Email_nauczyciela"] != "" else None
                    courses_list.append(
                        Courses(
                            name=row["Nazwa"],
                            teacher_id=teacher,
                            description=row["Opis"]
                        )
                    )
                    courses_names.append(row["Nazwa"])
                except People.DoesNotExist:
                    ...
        Courses.objects.bulk_create(courses_list, ignore_conflicts=True)
        semesters_list = []
        for row in data:
            try:
                semester = Semesters.objects.get(name=row["Semestr"], course_id__name=row["Nazwa"])
            except Semesters.DoesNotExist:
                try:
                    course = Courses.objects.get(name=row["Nazwa"])
                    semesters_list.append(
                        Semesters(
                            course_id=course,
                            name=row["Semestr"]
                        )
                    )
                except Courses.DoesNotExist:
                    ...
        Semesters.objects.bulk_create(semesters_list)


class EventsAttendeesView(ConcreteBrowseView, NavigationBar):
    active_nav_items = ["Wydarzenia", "Przeglądaj", "Szczegóły o uczestnikach"]
    nav_bars = [BROWSE_NAV_ITEMS, EVENT_NAV_ITEMS, CON_EVENT_NAV_ITEMS]
    template_name = "events/attendees.html"

    def get(self, request, fpk):
        obj = Events.objects.get(id=fpk)
        no_attendees = Events.objects.values('attendees__group__category_id').annotate(no_attendees=Sum('attendees__no_attendees')).order_by('-no_attendees').filter(id=fpk).first()
        attendees = self.group_attendees(SelectAttendees.objects.filter(event=fpk))
        self._activate_nav_item()
        nav_bars = self._set_nav_bars([obj], 2, fpk=fpk)
        context = {'object': obj, 'attendees': attendees, 'nav_bars': nav_bars, 'no_attendees': no_attendees}
        return render(request, self.template_name, context)

    def group_attendees(self, attendees):
        sorted = {}
        for atendee in attendees:
            if atendee.category not in sorted.keys():
                sorted[atendee.category] = []
            sorted[atendee.category].append(atendee)
        return sorted


class SemestersDatesView(ConcreteBrowseView):
    active_nav_items = ["Kursy Językowe", "Semestry", "Terminy"]
    nav_bars = [BROWSE_NAV_ITEMS, COURSES_NAV_ITEMS, SEMESTERS_NAV_ITEMS]
    header_cells = [
        HeaderCell("Data", 0, "th0", True),
        HeaderCell("Godzina rozpoczęcia", 1, "th1", True),
        HeaderCell("Godzina zakończenia", 2, "th2", True),
        HeaderCell("Opcje", None, None, False)
    ]
    filter_form = SemesterDateFilter

    def _get_fields(self, objects, **kwargs):
        return [HTMLRow([
                DataCell('date', o.date),
                DataCell('time', o.start_time),
                DataCell('time', o.end_time),
                DataCell('link', [Link("Zobacz obecności", "btn btn-info btn-sm", f"/course/{o.course_id.id}/semester/{o.semester_id.id}/dates/{o.date_id}"),
                                  Link("Usuń", "btn btn-danger btn-sm", f"/course/{o.course_id.id}/semester/{o.semester_id.id}/dates/{o.date_id}/delete")])
                ], onclick=f"/course/{o.course_id.id}/semester/{o.semester_id.id}/dates/{o.date_id}", id=o.date_id) for o in objects]

    def _get_buttons(self, **kwargs):
        return [Button("Dodaj datę", f"/course/{kwargs['fpk']}/semester/{kwargs['spk']}/add_date")]

    def _get_objects(self, instance, query, **kwargs):
        q = query.pop('q') if 'q' in query else ''
        kw = format_filter_query(query)
        return SemesterDates.objects.filter(Q(course_id=kwargs['fpk'], semester_id=kwargs['spk'], date__icontains=q), **kw)

    def _get_instances(self, **kwargs):
        return [Courses.objects.get(id=kwargs['fpk']), Semesters.objects.get(course_id=kwargs['fpk'], id=kwargs['spk'])]

    def _get_MtM_instances(self, ids, **kwargs):
        return SemesterDates.objects.filter(course_id=kwargs['fpk'], semester_id=kwargs['spk'], date_id__in=ids)


class SemestersDataEditView(TemplateView, NavigationBar):
    template_name = "add_from_form.html"
    extend_file = "browse/main.html"
    nav_bars = [BROWSE_NAV_ITEMS, COURSES_NAV_ITEMS, SEMESTERS_NAV_ITEMS]
    active_nav_items = ["Kursy Językowe", "Semestry", "Dane"]

    def post(self, request, fpk, spk):
        Semesters.objects.filter(course_id=fpk, id=spk).update(
            name=request.POST.get('name'),
            description=request.POST.get('description')
        )
        return redirect(request.POST.get('referer'))

    def get(self, request, fpk, spk):
        course = Courses.objects.get(id=fpk)
        semester = Semesters.objects.get(course_id=fpk, id=spk)
        form = SemesterFormEdit(instance=semester)
        self._activate_nav_item()
        nav_bars = self._set_nav_bars([course, semester], fpk=fpk, spk=spk)
        context = {'object': course, 'semester': semester, 'form': form, "extend_file": self.extend_file, 'nav_bars': nav_bars}
        return render(request, self.template_name, context)


class SemestersAttendeesView(ConcreteBrowseView):
    # TODO add teacher
    active_nav_items = ["Kursy Językowe", "Semestry", "Uczestnicy"]
    nav_bars = [BROWSE_NAV_ITEMS, COURSES_NAV_ITEMS, SEMESTERS_NAV_ITEMS]
    header_cells = [
        HeaderCell("Uczestnik", 0, "th0", True),
        HeaderCell("Opcje", None, None, False)
    ]

    def _get_fields(self, objects, **kwargs):
        return [HTMLRow([
                DataCell('data', o.person_id),
                DataCell('link', [Link("Zobacz uczestnika", "btn btn-info btn-sm", f"/person/{o.person_id.id}/data"),
                                  # TODO Zobacz obecności Link("Zobacz obecności", "btn btn-info btn-sm", f"/person/{o.person_id.id}/data"),
                                  Link("Wypisz", "btn btn-danger btn-sm", f"/course/{kwargs['fpk']}/semester/{kwargs['spk']}/person/{o.person_id.id}/delete_attendance")])
                ], onclick=f"/person/{o.person_id.id}/data", id=o.person_id.id) for o in objects]

    def _get_buttons(self, **kwargs):
        return [Button("Dodaj Uczestnika", f"/course/{kwargs['fpk']}/semester/{kwargs['spk']}/add_attendee")]

    def _get_objects(self, instance, query, **kwargs):
        q = query.pop('q') if 'q' in query else ''
        kw = format_filter_query(query)
        q_args = q.split(' ')
        q_name = q_args[0]
        q_surname = q_args[1] if len(q_args) > 1 else ''
        q_pcode = q_args[2] if len(q_args) > 2 else ''
        return PeopleSemesters.objects.filter(Q(course_id=kwargs['fpk'], semester_id=kwargs['spk'], person_id__name__icontains=q_name, person_id__surname__icontains=q_surname, person_id__pcode__icontains=q_pcode), **kw)

    def _get_instances(self, **kwargs):
        return [Courses.objects.get(id=kwargs['fpk']), Semesters.objects.get(course_id=kwargs['fpk'], id=kwargs['spk'])]

    def _get_MtM_instances(self, ids, **kwargs):
        return PeopleSemesters.objects.filter(course_id=kwargs['fpk'], semester_id=kwargs['spk'], person_id__id__in=ids)


class EventsAttendanceView(ConcreteBrowseView):
    active_nav_items = ["Wydarzenia", "Przeglądaj", "Obecność"]
    nav_bars = [BROWSE_NAV_ITEMS, EVENT_NAV_ITEMS, CON_EVENT_NAV_ITEMS]
    header_cells = [
        HeaderCell("Uczestnik", 0, "th0", True),
        HeaderCell("Obecność", 1, "th1", True),
        HeaderCell("Opcje", None, None, False)
    ]
    first_setable_bar = 2

    def _get_fields(self, objects, **kwargs):
        return [HTMLRow([
                DataCell('data', o.person_id),
                DataCell('data', o.attendance_type),
                DataCell('link', [Link("Zobacz uczestnika", "btn btn-info btn-sm", f"/person/{o.person_id.id}/data"),
                                  # TODO Zobacz obecności Link("Zobacz obecności", "btn btn-info btn-sm", f"/person/{o.person_id.id}/data"),
                                  Link("Wypisz", "btn btn-danger btn-sm", f"/events/{o.event_id.id}/person/{o.person_id.id}/delete_attendance")])
                ], onclick=f"/person/{o.person_id.id}/data", id=o.person_id.id) for o in objects]

    def _get_buttons(self, **kwargs):
        return [Button("Dodaj uczestnika", f"/events/{kwargs['fpk']}/add_attendee"),
                Button("Edytuj obecności", f"/events/{kwargs['fpk']}/edit_attendance")]

    def _get_instances(self, **kwargs):
        return [Events.objects.get(id=kwargs['fpk'])]

    def _get_objects(self, instances, query, **kwargs):
        q = query.pop('q') if 'q' in query else ''
        kw = format_filter_query(query)
        q_args = q.split(' ')
        q_name = q_args[0]
        q_surname = q_args[1] if len(q_args) > 1 else ''
        q_pcode = q_args[2] if len(q_args) > 2 else ''
        return PeopleEvents.objects.filter(Q(event_id=kwargs['fpk'], person_id__name__icontains=q_name, person_id__surname__icontains=q_surname, person_id__pcode__icontains=q_pcode), **kw)

    def _get_MtM_instances(self, ids, **kwargs):
        return PeopleEvents.objects.filter(event_id=kwargs['fpk'], person_id__id__in=ids)


class EventsEditAttendanceView(TemplateView, NavigationBar):
    template_name = "events/attendance_edit.html"
    active_nav_items = ["Wydarzenia", "Przeglądaj", "Obecność"]
    nav_bars = [BROWSE_NAV_ITEMS, EVENT_NAV_ITEMS, CON_EVENT_NAV_ITEMS]
    first_setable_bar = 2

    def get(self, request, fpk):
        event = Events.objects.get(id=fpk)
        attendance = PeopleEvents.objects.filter(event_id=fpk)
        forms = [EditAttendanceFromDate(instance=att) for att in attendance]
        self._activate_nav_item()
        nav_bars = self._set_nav_bars([event], first_setable_bar=self.first_setable_bar, fpk=fpk)
        context = {'objects': forms, 'nav_bars': nav_bars, 'event': event}
        return render(request, self.template_name, context)

    def post(self, request, fpk):
        attendance_types = request.POST.getlist('attendance_type')
        pids = request.POST.getlist('person_id')
        for pid, att in zip(pids, attendance_types):
            PeopleEvents.objects.filter(event_id=fpk, person_id=pid).update(attendance_type=att)
        return redirect(request.POST.get('referer'))

    def _get_objects(self, instance, query, **kwargs):
        q = query.pop('q') if 'q' in query else ''
        kw = format_filter_query(query)
        q_args = q.split(' ')
        q_name = q_args[0]
        q_surname = q_args[1] if len(q_args) > 1 else ''
        q_pcode = q_args[2] if len(q_args) > 2 else ''
        return PeopleEvents.objects.filter(Q(event_id=kwargs['fpk'], person_id__name__icontains=q_name, person_id__surname__icontains=q_surname, person_id__pcode__icontains=q_pcode), **kw)

    def _get_instances(self, **kwargs):
        return [Events.objects.get(id=kwargs['fpk'])]


class ProjectsCodesView(ConcreteBrowseView):
    active_nav_items = ["Projekty", "Kody"]
    nav_bars = [BROWSE_NAV_ITEMS, PROJECTS_NAV_ITEMS]
    header_cells = [
        HeaderCell("Kod", 0, "th0", True),
        HeaderCell("Rodzaj", 1, "th1", True),
        HeaderCell("Nazwa rodzaju aktywności/ wydarzenia", 2, "th2", True),
        HeaderCell("Opcje", None, None, False)
    ]
    filter_form = CodeFilter

    def _get_fields(self, objects, **kwargs):
        return [HTMLRow([
                DataCell('data', o.code),
                DataCell('data', o.type),
                DataCell('data', o.name),
                DataCell('link', [Link("Edytuj", "btn btn-info btn-sm", f"/projects/{kwargs['fpk']}/codes/{o.cid}/edit"),
                                  Link("Usuń", "btn btn-danger btn-sm", f"/projects/{kwargs['fpk']}/codes/{o.cid}/delete")])
                ], id=o.cid) for o in objects]

    def _get_buttons(self, **kwargs):
        return [Button("Dodaj kod", f"/projects/{kwargs['fpk']}/add_code")]

    def _get_objects(self, instance, query, **kwargs):
        if 'type' not in query.keys():
            if len(query.keys()) == 0:
                query['type'] = ['activity_type', 'event_type']
            else:
                query['type'] = []
        q = query.pop('q') if 'q' in query else ''
        query = dict(query)
        type = query.pop('type')
        name = query.pop('event_or_activity_type_name') if 'event_or_activity_type_name' in query.keys() else ''
        kw = format_filter_query(query)
        for t in ['event_type', 'activity_type']:
            if t not in type:
                kw[t + '__isnull'] = True
        return Codes.objects.filter(
            Q(project_id=kwargs['fpk'], code__icontains=q) |
            Q(project_id=kwargs['fpk'], event_type__name__icontains=q) |
            Q(project_id=kwargs['fpk'], activity_type__name__icontains=q),
            Q(project_id=kwargs['fpk'], event_type__name__icontains=name) |
            Q(project_id=kwargs['fpk'], activity_type__name__icontains=name), **kw)

    def _get_instances(self, **kwargs):
        return [Projects.objects.get(id=kwargs['fpk'])]

    def _get_MtM_instances(self, ids, **kwargs):
        return Codes.objects.filter(project_id=kwargs['fpk'], cid__in=ids)


class CodesDataEditView(TemplateView, NavigationBar):
    template_name = "add_from_form.html"
    extend_file = "projects/main.html"
    active_nav_items = ["Projekty", "Kody"]
    nav_bars = [BROWSE_NAV_ITEMS, PROJECTS_NAV_ITEMS]

    def post(self, request, fpk, spk):
        Codes.objects.filter(project_id=fpk, cid=spk).update(
            code=request.POST.get('code'),
            event_type=request.POST.get('event_type'),
            activity_type=request.POST.get('activity_type'),
            additional_checks=request.POST.get('additional_checks')
        )
        return redirect(request.POST.get('referer'))

    def get(self, request, fpk, spk):
        project = Projects.objects.get(id=fpk)
        code = Codes.objects.get(project_id=fpk, cid=spk)
        form = CodesForm(instance=code)
        self._activate_nav_item()
        nav_bars = self._set_nav_bars([project, code], fpk=fpk, spk=spk)
        context = {'object': project, 'code': code, 'form': form, "extend_file": self.extend_file, 'nav_bars': nav_bars}
        return render(request, self.template_name, context)


class BrowseSemesterDatesView(ConcreteBrowseView):
    # TODO add teacher
    active_nav_items = ["Kursy Językowe", "Semestry", "Terminy", ""]
    nav_bars = [BROWSE_NAV_ITEMS, COURSES_NAV_ITEMS, SEMESTERS_NAV_ITEMS, []]
    header_cells = [
        HeaderCell("Uczestnik", 0, "th0", True),
        HeaderCell("Obecność", 1, "th1", True)
    ]

    def _get_fields(self, objects, **kwargs):
        return [HTMLRow([
                DataCell('data', o.person_id),
                DataCell('data', o.attendance_type)
                ], id=o.person_id.id) for o in objects]

    def _get_buttons(self, **kwargs):
        return [Button("Edytuj", f"/course/{kwargs['fpk']}/semester/{kwargs['spk']}/dates/{kwargs['tpk']}/edit")]

    def _get_objects(self, instance, query, **kwargs):
        q = query.pop('q') if 'q' in query else ''
        kw = format_filter_query(query)
        return Attendance.objects.filter(Q(course_id=kwargs['fpk'], semester_id=kwargs['spk'], date_id=kwargs['tpk']), **kw)

    def _get_instances(self, **kwargs):
        return [Courses.objects.get(id=kwargs['fpk']), Semesters.objects.get(course_id=kwargs['fpk'], id=kwargs['spk']), SemesterDates.objects.get(course_id=kwargs['fpk'], semester_id=kwargs['spk'], date_id=kwargs['tpk'])]

    def _get_MtM_instances(self, ids, **kwargs):
        return Attendance.objects.filter(course_id=kwargs['fpk'], semester_id=kwargs['spk'], date_id=kwargs['tpk'], person_id__id__in=ids)


class EditAttendanceView(TemplateView, NavigationBar):
    template_name = "semesters/attendance_edit.html"
    nav_bars = [BROWSE_NAV_ITEMS, COURSES_NAV_ITEMS, SEMESTERS_NAV_ITEMS, []]
    active_nav_items = ['Kursy', 'Semestry', 'Terminy', '']

    def get(self, request, fpk, spk, tpk):
        course = Courses.objects.get(id=fpk)
        semester = Semesters.objects.get(course_id=fpk, id=spk)
        date = SemesterDates.objects.get(course_id=fpk, semester_id=spk, date_id=tpk)
        attendance = Attendance.objects.filter(course_id=fpk, semester_id=spk, date_id=tpk)
        forms = [EditAttendanceFromDate(instance=att) for att in attendance]
        self._activate_nav_item()
        nav_bars = self._set_nav_bars([course, semester, date], fpk=fpk, spk=spk, tpk=tpk)
        context = {'object': course, 'semester': semester, 'date': date, 'objects': forms, 'nav_bars': nav_bars}
        return render(request, self.template_name, context)

    def post(self, request, fpk, spk, tpk):
        attendance_types = request.POST.getlist('attendance_type')
        pids = request.POST.getlist('person_id')
        for pid, att in zip(pids, attendance_types):
            Attendance.objects.filter(course_id=fpk, semester_id=spk, date_id=tpk, person_id=pid).update(attendance_type=att)
        return redirect(request.POST.get('referer'))


class DeleteSemesterDates(TemplateView):
    template_name = "delete.html"

    def get(self, request, fpk, spk, tpk):
        object = SemesterDates.objects.get(course_id=fpk, semester_id=spk, date_id=tpk)
        context = {'obj': object}
        return render(request, self.template_name, context)

    def post(self, request, fpk, spk, tpk):
        SemesterDates.objects.filter(course_id=fpk, semester_id=spk, date_id=tpk).delete()
        return redirect(request.POST.get('referer'))


class DeleteAttendant(TemplateView):
    template_name = "delete.html"

    def get(self, request, fpk, spk, tpk):
        object = PeopleSemesters.objects.get(course_id=fpk, semester_id=spk, person_id=tpk)
        context = {'obj': object}
        return render(request, self.template_name, context)

    def post(self, request, fpk, spk, tpk):
        PeopleSemesters.objects.filter(course_id=fpk, semester_id=spk, person_id=tpk).delete()
        return redirect(request.POST.get('referer'))


class ActivityDataView(TemplateView, NavigationBar):
    template_name = "activity/data.html"
    active_nav_items = ["Osoby", "Aktywności", ""]
    nav_bars = [BROWSE_NAV_ITEMS, PERSON_NAV_ITEMS, []]
    first_setable_bar = 1

    def get(self, request, fpk, spk, tpk):
        person = People.objects.get(id=fpk)
        activity = Activities.objects.get(person_id=fpk, activity_type_id=spk, activity_id=tpk)
        form = ActivitiesViewForm(instance=activity)
        form.disable(['__all'])
        self._activate_nav_item()
        nav_bars = self._set_nav_bars([person, activity], self.first_setable_bar, fpk=fpk, spk=spk, tpk=tpk)
        context = {'person': person, 'form': form, 'activity': activity, 'semester': activity.semester_id, 'nav_bars': nav_bars}
        return render(request, self.template_name, context)


class ActivityDataEditView(TemplateView, NavigationBar):
    template_name = "add_from_form.html"
    extend_file = "activity/main.html"
    nav_bars = [BROWSE_NAV_ITEMS, PERSON_NAV_ITEMS, []]
    active_nav_items = ["Osoby", "Aktywności", ""]

    def get(self, request, fpk, spk, tpk):
        person = People.objects.get(id=fpk)
        activity_type = ActivityTypes.objects.get(id=spk)
        activity = Activities.objects.get(person_id=fpk, activity_type_id=spk, activity_id=tpk)
        form = ActivitiesForm(instance=activity)
        self._activate_nav_item()
        nav_bars = [BROWSE_NAV_ITEMS, [NavItem(str(person), isActive=False, isDisabled=True)], [NavItem(str(activity), isActive=False, isDisabled=True)]]
        for item in self.nav_bars[1]:
            nav_bars[1].append(NavItem(name=item.name, href=item.href % fpk, isActive=item.isActive, isDisabled=item.isDisabled))
        for item in self.nav_bars[2]:
            nav_bars[2].append(NavItem(name=item.name, href=item.href % (fpk, spk, tpk), isActive=item.isActive, isDisabled=item.isDisabled))
        context = {'object': person, 'activity_type': activity_type, 'form': form, 'activity': activity, "extend_file": self.extend_file, 'nav_bars': nav_bars}
        return render(request, self.template_name, context)

    def post(self, request, fpk, spk, tpk):
        form = ActivitiesForm(data=request.POST)
        if form.is_valid():
            if form['checkbox'].value():
                Activities.objects.filter(person_id=fpk, activity_type_id=spk, activity_id=tpk).update(
                    activity_type_id=request.POST.get('activity_type_id'),
                    notes=request.POST.get('notes'),
                    course_id=request.POST.get('course_id'),
                    semester_id=request.POST.get('semester_id'),
                )
            else:
                Activities.objects.filter(person_id=fpk, activity_type_id=spk, activity_id=tpk).update(
                    activity_type_id=request.POST.get('activity_type_id'),
                    notes=request.POST.get('notes'),
                    course_id=None,
                    semester_id=None,
                )
        return redirect(f"/person/{fpk}/activity_type/{request.POST.get('activity_type_id')}/activity/{tpk}/data")


class ConsentDataView(TemplateView):
    template_name = "person/consent.html"

    def get(self, request, fpk, spk):
        person = People.objects.get(id=fpk)
        consent = Consents.objects.get(person_id=fpk, consent_id=spk)
        form = ConsentsForm(instance=consent)
        form.disable(["__all"])
        context = {'object': person, 'consent': consent, 'form': form}
        return render(request, self.template_name, context)


class ConsentDataEditView(TemplateView):
    template_name = "add_from_form.html"
    extend_file = "person/main.html"

    def get(self, request, fpk, spk):
        person = People.objects.get(id=fpk)
        consent = Consents.objects.get(person_id=fpk, consent_id=spk)
        form = ConsentsForm(instance=consent)
        context = {'object': person, 'consent': consent, 'form': form, "extend_file": self.extend_file}
        return render(request, self.template_name, context)

    def post(self, request, fpk, spk):
        Consents.objects.filter(person_id=fpk, consent_id=spk).update(
            address=request.POST.get('address'),
            notes=request.POST.get('notes')
        )
        return redirect(request.POST.get('referer'))


def combine_filters(query, filters):
    for filter in filters:
        query = query.filter(**filter)
    return query.count()


class ProjectsRaportView(TemplateView, NavigationBar):
    template_name = "projects/raport.html"
    active_nav_items = ["Projekty", "Raport"]
    nav_bars = [BROWSE_NAV_ITEMS, PROJECTS_NAV_ITEMS]

    def get(self, request, fpk):
        project = Projects.objects.get(id=fpk)
        self._activate_nav_item()
        nav_bars = self._set_nav_bars([project], fpk=fpk)
        context = {'nav_bars': nav_bars, 'ready': 0, 'form': ReportForm}
        return render(request, self.template_name, context)

    def post(self, request, fpk):
        codes = Codes.objects.filter(project_id=fpk)
        start = request.POST.get('since')
        end = request.POST.get('to')
        with open('__tmp.csv', 'w', newline='') as f:
            raport_writer = writer(f, delimiter=';', quotechar='|')
            raport_writer.writerow(['Kod', 'Liczba'])
            report_dict = dict()
            for code in codes:
                if code.code not in report_dict.keys():
                    report_dict[code.code] = {"_all": 0}
                if code.activity_type is not None:
                    rules_kwargs = {}
                    rules_args = []
                    if code.additional_checks is not None and '=' in code.additional_checks:
                        rules = code.additional_checks.split('\n')
                        rules = [r.strip().replace(' ', '').split('=') for r in rules]
                        for r in rules:
                            if r[0] == 'Czypełnoletni':
                                rules_kwargs['person_id__is_adult__icontains'] = {"Tak": 'true', "Nie": 'false'}[r[1]]
                            elif r[0] == 'Kraj':
                                rules_kwargs['person_id__country_code__icontains'] = r[1]
                            elif r[0] == 'Dodatkowe':
                                for additional in r[1].split(','):
                                    rules_args.append({'person_id__description__icontains': additional})
                    activities = Activities.objects.filter(activity_type_id=code.activity_type, date__range=[start, end], **rules_kwargs)
                    activities = combine_filters(activities, rules_args)
                    genders = Genders.objects.all()
                    report_dict[code.code]["_all"] += activities
                    for gender in genders:
                        activities = Activities.objects.filter(activity_type_id=code.activity_type, date__range=[start, end], person_id__gender=gender, **rules_kwargs)
                        activities = combine_filters(activities, rules_args)
                        report_dict[code.code][gender.name] = activities
                elif code.event_type is not None:
                    events = Events.objects.filter(id_event_type=code.event_type, date__range=[start, end]).count()
                    report_dict[code.code]["_all"] += events
            for k, v in report_dict.items():
                for by_gender_key, by_gender_value in v.items():
                    if by_gender_key == "_all":
                        raport_writer.writerow([k, by_gender_value])
                    elif by_gender_value > 0:
                        raport_writer.writerow([f"W tym {by_gender_key}", by_gender_value])
        project = Projects.objects.get(id=fpk)
        with open('__tmp.csv', 'rb') as f:
            response = FileResponse(open('__tmp.csv', 'rb'), as_attachment=True, filename=f'{project.name}_raport.csv')
            return response
        return redirect(f'/projects/{fpk}/data')
