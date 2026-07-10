from nomad.config.models.plugins import AppEntryPoint
from nomad.config.models.ui import (
    App,
    Column,
    Dashboard,
    Layout,
    Menu,
    MenuItemTerms,
    Pagination,
    Rows,
    SearchQuantities,
    WidgetTerms,
)

SCHEMA = 'fairmat_members.schema_packages.schema_package.Person'

# ---------------------------------------------------------------------------
# Search quantity paths
# ---------------------------------------------------------------------------
Q_LAST_NAME = f'data.last_name#{SCHEMA}'
Q_FIRST_NAME = f'data.first_name#{SCHEMA}'
Q_MEMBER_TYPE = f'data.member_type#{SCHEMA}'
Q_EXPERTISE = f'data.expertise#{SCHEMA}'
Q_INSTITUTION = f'data.affiliations.institution_name#{SCHEMA}'
Q_CITY = f'data.affiliations.city#{SCHEMA}'
Q_COUNTRY = f'data.affiliations.country#{SCHEMA}'
Q_ROLE = f'data.fairmat_roles.role#{SCHEMA}'
Q_AREA = f'data.fairmat_roles.area#{SCHEMA}'
Q_PROJECT_NAME = f'data.external_projects.project_name#{SCHEMA}'
Q_PROJECT_TYPE = f'data.external_projects.project_type#{SCHEMA}'
Q_MAILING_LIST = f'data.mailing_lists#{SCHEMA}'

# ---------------------------------------------------------------------------
# App definition
# ---------------------------------------------------------------------------
fairmat_members_app = App(
    label='FAIRmat Members',
    path='fairmat-members',
    category='FAIRmat',
    description=(
        'Browse and filter the FAIRmat member directory: '
        'PIs, staff, collaborators, affiliations, roles, and external projects.'
    ),
    filters_locked={
        'section_defs.definition_qualified_name': [SCHEMA],
    },
    pagination=Pagination(
        order_by='upload_create_time',
        order='desc',
        page_size=20,
    ),
    search_quantities=SearchQuantities(
        include=[
            Q_LAST_NAME,
            Q_FIRST_NAME,
            Q_MEMBER_TYPE,
            Q_EXPERTISE,
            Q_INSTITUTION,
            Q_CITY,
            Q_COUNTRY,
            Q_ROLE,
            Q_AREA,
            Q_PROJECT_NAME,
            Q_PROJECT_TYPE,
            Q_MAILING_LIST,
        ]
    ),
    columns=[
        Column(search_quantity=Q_LAST_NAME, title='Last name', selected=True),
        Column(search_quantity=Q_FIRST_NAME, title='First name', selected=True),
        Column(search_quantity=Q_MEMBER_TYPE, title='Member type', selected=True),
        Column(search_quantity=Q_ROLE, title='FAIRmat role', selected=True),
        Column(search_quantity=Q_AREA, title='Area', selected=True),
        Column(search_quantity=Q_INSTITUTION, title='Institution', selected=False),
        Column(search_quantity=Q_COUNTRY, title='Country', selected=False),
        Column(search_quantity=Q_EXPERTISE, title='Expertise', selected=False),
        Column(search_quantity=Q_PROJECT_TYPE, title='External project type', selected=False),
    ],
    rows=Rows(),
    menu=Menu(
        title='Filters',
        items=[
            Menu(
                title='Name',
                items=[
                    MenuItemTerms(
                        search_quantity=Q_LAST_NAME,
                        title='Last name',
                        show_input=True,
                        options=20,
                    ),
                    MenuItemTerms(
                        search_quantity=Q_FIRST_NAME,
                        title='First name',
                        show_input=True,
                        options=20,
                    ),
                ],
            ),
            Menu(
                title='Member type',
                items=[
                    MenuItemTerms(
                        search_quantity=Q_MEMBER_TYPE,
                        title='Type',
                        show_input=False,
                        options=5,
                    ),
                ],
            ),
            Menu(
                title='FAIRmat role',
                items=[
                    MenuItemTerms(
                        search_quantity=Q_ROLE,
                        title='Role',
                        show_input=False,
                        options=10,
                    ),
                    MenuItemTerms(
                        search_quantity=Q_AREA,
                        title='Area',
                        show_input=False,
                        options=10,
                    ),
                ],
            ),
            Menu(
                title='Institution',
                items=[
                    MenuItemTerms(
                        search_quantity=Q_INSTITUTION,
                        title='Institution name',
                        show_input=True,
                        options=20,
                    ),
                    MenuItemTerms(
                        search_quantity=Q_COUNTRY,
                        title='Country',
                        show_input=True,
                        options=20,
                    ),
                ],
            ),
            Menu(
                title='External projects',
                items=[
                    MenuItemTerms(
                        search_quantity=Q_PROJECT_TYPE,
                        title='Project type',
                        show_input=False,
                        options=10,
                    ),
                    MenuItemTerms(
                        search_quantity=Q_PROJECT_NAME,
                        title='Project name',
                        show_input=True,
                        options=20,
                    ),
                ],
            ),
            Menu(
                title='Expertise',
                items=[
                    MenuItemTerms(
                        search_quantity=Q_EXPERTISE,
                        title='Expertise keyword',
                        show_input=True,
                        options=20,
                    ),
                ],
            ),
            Menu(
                title='Mailing lists',
                items=[
                    MenuItemTerms(
                        search_quantity=Q_MAILING_LIST,
                        title='Mailing list',
                        show_input=True,
                        options=20,
                    ),
                ],
            ),
        ],
    ),
    dashboard=Dashboard(
        widgets=[
            WidgetTerms(
                title='Members by type',
                type='terms',
                search_quantity=Q_MEMBER_TYPE,
                scale='linear',
                show_input=False,
                layout={
                    'lg': Layout(h=6, w=4, x=0, y=0),
                    'md': Layout(h=6, w=6, x=0, y=0),
                    'sm': Layout(h=6, w=12, x=0, y=0),
                },
            ),
            WidgetTerms(
                title='Members by FAIRmat role',
                type='terms',
                search_quantity=Q_ROLE,
                scale='linear',
                show_input=False,
                layout={
                    'lg': Layout(h=6, w=4, x=4, y=0),
                    'md': Layout(h=6, w=6, x=6, y=0),
                    'sm': Layout(h=6, w=12, x=0, y=6),
                },
            ),
            WidgetTerms(
                title='Members by area',
                type='terms',
                search_quantity=Q_AREA,
                scale='linear',
                show_input=False,
                layout={
                    'lg': Layout(h=6, w=4, x=8, y=0),
                    'md': Layout(h=6, w=6, x=0, y=6),
                    'sm': Layout(h=6, w=12, x=0, y=12),
                },
            ),
            WidgetTerms(
                title='Members by country',
                type='terms',
                search_quantity=Q_COUNTRY,
                scale='linear',
                show_input=False,
                layout={
                    'lg': Layout(h=6, w=6, x=0, y=6),
                    'md': Layout(h=6, w=6, x=6, y=6),
                    'sm': Layout(h=6, w=12, x=0, y=18),
                },
            ),
            WidgetTerms(
                title='External project types',
                type='terms',
                search_quantity=Q_PROJECT_TYPE,
                scale='linear',
                show_input=False,
                layout={
                    'lg': Layout(h=6, w=6, x=6, y=6),
                    'md': Layout(h=6, w=6, x=0, y=12),
                    'sm': Layout(h=6, w=12, x=0, y=24),
                },
            ),
        ]
    ),
)

app_entry_point = AppEntryPoint(
    name='FAIRmatMembersApp',
    description='Search and browse the FAIRmat member directory.',
    app=fairmat_members_app,
)
