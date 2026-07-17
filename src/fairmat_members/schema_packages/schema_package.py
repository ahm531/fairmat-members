from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nomad.datamodel.datamodel import EntryArchive
    from structlog.stdlib import BoundLogger

from fairmat_onboarding.schema_packages.schema_package import (
    PIOnboardingQuestionnaire,
)
from nomad.config import config
from nomad.datamodel.data import ArchiveSection, Schema, UseCaseElnCategory
from nomad.datamodel.metainfo.annotations import ELNAnnotation, ELNComponentEnum
from nomad.metainfo import (
    MEnum,
    Quantity,
    SchemaPackage,
    Section,
    SubSection,
)

configuration = config.get_plugin_entry_point(
    'fairmat_members.schema_packages:schema_package_entry_point'
)

m_package = SchemaPackage()

# ---------------------------------------------------------------------------
# Controlled vocabularies
# ---------------------------------------------------------------------------

MEMBER_TYPE = MEnum(
    'PI',
    'Coworker',
    'Coordinator',
    'Collaborator',
    'External',
    'Alumni',
)

FAIRMAT_ROLE_VOCAB = MEnum(
    'Area Leader',
    'Deputy Area Leader',
    'Task Leader',
    'Participant',
    'Member',
    'Area Coordinator',
    'Technical Coordinator',
    'Scientific Coordinator',
)

FAIRMAT_AREA = MEnum(
    'Area A',
    'Area B',
    'Area C',
    'Area D',
    'Area E',
    'Area F',
    'Area G',
    'Area H',
)

PROJECT_TYPE = MEnum(
    'CRC',
    'RTG',
    'FOR',
    'Cluster of Excellence',
    'Industry',
    'NFDI Initiative',
    'International Initiative',
    'EU Project',
    'Infrastructure Project',
    'Other',
)

# NOTE: an MEnum instance binds to a single quantity definition (its shape is
# taken from that definition), so it must NOT be shared between quantities
# with different shapes.  Keep the raw values in a plain list and construct a
# fresh MEnum per quantity.
MAILING_LISTS = [
    'fairmat-area-leaders@listen.physik.hu-berlin.de',
    'fairmat-coordinators@listen.physik.hu-berlin.de',
    'fairmat-hq@listen.physik.hu-berlin.de',
    'fairmat-team@listen.physik.hu-berlin.de',
    'fairmat-coworkers@listen.physik.hu-berlin.de',
    'fairmat2-area-a@listen.physik.hu-berlin.de',
    'fairmat2-area-b@listen.physik.hu-berlin.de',
    'fairmat2-area-c@listen.physik.hu-berlin.de',
    'fairmat2-area-d@listen.physik.hu-berlin.de',
    'fairmat2-area-e@listen.physik.hu-berlin.de',
    'fairmat2-area-f@listen.physik.hu-berlin.de',
    'fairmat2-area-g@listen.physik.hu-berlin.de',
    'fairmat2-pi@listen.physik.hu-berlin.de',
]

INVITED_TO = MEnum(
    'Project Meeting',
    'Users Meeting',
    'Both',
)

REIMBURSEMENT = MEnum(
    'All events',
    'Requires approval',
    'No',
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _unique_clean(values) -> list[str]:
    out: list[str] = []
    for value in values or []:
        if value is None:
            continue
        cleaned = value.strip() if isinstance(value, str) else value
        if not cleaned:
            continue
        if cleaned not in out:
            out.append(cleaned)
    return out


# ---------------------------------------------------------------------------
# Sub-sections
# ---------------------------------------------------------------------------


class ExpertiseTerm(ArchiveSection):
    """Search-indexable mirror of a single expertise keyword.

    The app cannot use the list-valued `expertise` quantity as a search
    quantity, so `Person.normalize` mirrors it into this repeating
    subsection with a scalar `value`.
    """

    m_def = Section(a_eln={'hide': ['value']})
    value = Quantity(type=str)


class MailingListTerm(ArchiveSection):
    """Search-indexable mirror of a single mailing list subscription."""

    m_def = Section(a_eln={'hide': ['value']})
    value = Quantity(type=MEnum(MAILING_LISTS))


class Affiliation(ArchiveSection):
    """Organizational affiliation of a FAIRmat member."""

    m_def = Section(label_quantity='institution_name')

    institution_name = Quantity(
        type=str,
        label='Institution name',
        description='Name of the institution or organization.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
    )

    department = Quantity(
        type=str,
        label='Department',
        description='Department or group within the institution.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
    )

    city = Quantity(
        type=str,
        label='City',
        description='City where the institution is located.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
    )

    country = Quantity(
        type=str,
        label='Country',
        description='Country where the institution is located.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
    )

    ror_id = Quantity(
        type=str,
        label='ROR ID',
        description=(
            'Research Organization Registry (ROR) identifier for the institution '
            '(format: https://ror.org/xxxxxxxxx).'
        ),
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
    )


class FAIRmatRoleAssignment(ArchiveSection):
    """A FAIRmat role held by a member within a specific area."""

    m_def = Section(label_quantity='role')

    role = Quantity(
        type=FAIRMAT_ROLE_VOCAB,
        label='Role',
        description='FAIRmat organizational role.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.EnumEditQuantity),
    )

    area = Quantity(
        type=FAIRMAT_AREA,
        label='Area',
        description='FAIRmat area associated with this role.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.EnumEditQuantity),
    )

    task = Quantity(
        type=str,
        label='Task',
        description='Specific task or responsibility within the area (optional).',
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
    )


class ExternalProject(ArchiveSection):
    """An external project or collaboration a FAIRmat member is involved in."""

    m_def = Section(label_quantity='project_name')

    project_name = Quantity(
        type=str,
        label='Project name',
        description='Name of the external project or initiative.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
    )

    project_type = Quantity(
        type=PROJECT_TYPE,
        label='Project type',
        description='Type or category of the external project.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.EnumEditQuantity),
    )

    role_in_project = Quantity(
        type=str,
        label='Role in project',
        description='Role or function of this person within the project.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
    )

    institution_or_partner = Quantity(
        type=str,
        label='Institution / partner',
        description='Institution or partner organization involved in this project.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
    )

    website = Quantity(
        type=str,
        label='Website',
        description='URL of the project website.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.URLEditQuantity),
    )

    notes = Quantity(
        type=str,
        label='Notes',
        description='Any additional notes about this project involvement.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
    )


class EventInvitation(ArchiveSection):
    """FAIRmat internal event invitation and reimbursement status for a member."""

    m_def = Section()

    invited_to = Quantity(
        type=INVITED_TO,
        label='Invited to',
        description='Which FAIRmat internal meetings this member is invited to.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.EnumEditQuantity),
    )

    reimbursement = Quantity(
        type=REIMBURSEMENT,
        label='Reimbursement',
        description='Reimbursement eligibility for FAIRmat event attendance.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.EnumEditQuantity),
    )

    notes = Quantity(
        type=str,
        label='Notes',
        description='Additional notes about event invitation or reimbursement.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
    )


# ---------------------------------------------------------------------------
# Main schema – Person
# ---------------------------------------------------------------------------


class Person(Schema):
    """
    Schema for a FAIRmat member profile.

    Captures identity, member type, expertise, institutional affiliations,
    FAIRmat organizational roles, external project involvement, and mailing
    list memberships.

    Future extensions (ORCID sync, ROR IDs, GitHub/LinkedIn
    profiles, publications, supervisor relationships, etc.) can be added as
    new quantities or subsections without breaking existing data.
    """

    m_def = Section(
        label='FAIRmat Member',
        categories=[UseCaseElnCategory],
        a_eln={
            'hide': ['lab_id', 'expertise_terms', 'mailing_list_terms'],
        },
    )

    # -- Identity -------------------------------------------------------------

    first_name = Quantity(
        type=str,
        label='First name',
        description='First (given) name of the member.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
    )

    last_name = Quantity(
        type=str,
        label='Last name',
        description='Last (family) name of the member.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
    )

    email = Quantity(
        type=str,
        label='Email',
        description='Primary email address of the member.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
    )

    orcid = Quantity(
        type=str,
        label='ORCID',
        description=(
            'ORCID identifier of the member '
            '(format: 0000-0000-0000-0000). '
            'Future versions may sync metadata automatically from orcid.org.'
        ),
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
    )

    onboarding_entries = Quantity(
        type=PIOnboardingQuestionnaire,
        shape=['*'],
        label='Onboarding entries',
        description=(
            'References to the PI onboarding questionnaire entries of this '
            'member. Filled automatically during processing by matching the '
            'member email against the NOMAD (Keycloak) account that created '
            'the questionnaire; additional entries can be linked manually.'
        ),
        a_eln=ELNAnnotation(component=ELNComponentEnum.ReferenceEditQuantity),
    )

    # -- Classification -------------------------------------------------------

    member_type = Quantity(
        type=MEMBER_TYPE,
        label='Member type',
        description='Category of membership within FAIRmat.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.EnumEditQuantity),
    )

    expertise = Quantity(
        type=str,
        shape=['*'],
        label='Expertise',
        description=(
            'Areas of scientific or technical expertise. '
            'Add one keyword or phrase per entry.'
        ),
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
    )

    # -- Subsections ----------------------------------------------------------

    affiliations = SubSection(
        section_def=Affiliation,
        label='Affiliations',
        description=(
            'Institutional affiliations of this member. '
            'Add one entry per affiliation. '
            'Future versions may resolve institution names via ROR identifiers.'
        ),
        repeats=True,
    )

    fairmat_roles = SubSection(
        section_def=FAIRmatRoleAssignment,
        label='FAIRmat roles',
        description='FAIRmat organizational roles held by this member.',
        repeats=True,
    )

    external_projects = SubSection(
        section_def=ExternalProject,
        label='External projects',
        description=(
            'External projects and collaborations this member is involved in.'
        ),
        repeats=True,
    )

    mailing_lists = Quantity(
        type=MEnum(MAILING_LISTS),
        shape=['*'],
        label='Mailing lists',
        description='FAIRmat mailing lists this member is subscribed to. Multiple selections allowed.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.AutocompleteEditQuantity),
    )

    # Hidden mirrors of the list-valued `expertise` and `mailing_lists`
    # quantities.  The scalar `value` inside these repeating subsections is
    # what the FAIRmat Members app uses for search, filtering, and columns
    # (list quantities are not allowed as app search quantities).
    expertise_terms = SubSection(section_def=ExpertiseTerm, repeats=True)
    mailing_list_terms = SubSection(section_def=MailingListTerm, repeats=True)

    event_invitation = SubSection(
        section_def=EventInvitation,
        label='Event invitation',
        description='Internal event invitation and reimbursement status for this member.',
    )

    notes = Quantity(
        type=str,
        label='Notes',
        description='Any additional notes about this member.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
    )

    def _find_onboarding_entries(self, archive, logger) -> list[str]:
        """Find all PIOnboardingQuestionnaire entries created by this member.

        The member's email is resolved to a NOMAD (Keycloak) account and the
        entry index is searched for questionnaires whose main author has that
        user_id.  Runs only server-side; in client/test contexts the lookup
        is skipped silently.  Questionnaires uploaded on behalf of a member
        carry the uploader's user_id and are NOT found — link those manually
        until the schemas carry an explicit user_id quantity.
        """
        if not self.email:
            return []
        try:
            from nomad.datamodel import User
            from nomad.search import search

            user = User.get(email=self.email.strip().lower())
            if user is None or not user.user_id:
                logger.info(
                    'no NOMAD account found for member email; '
                    'onboarding entries not linked',
                    member_email=self.email,
                )
                return []

            searcher_id = None
            if archive.metadata is not None and archive.metadata.main_author:
                searcher_id = archive.metadata.main_author.user_id
            results = search(
                owner='all',
                query={
                    'section_defs.definition_qualified_name': (
                        'fairmat_onboarding.schema_packages.'
                        'schema_package.PIOnboardingQuestionnaire'
                    ),
                    'main_author.user_id': user.user_id,
                },
                user_id=searcher_id,
            )
            return [
                f'../uploads/{entry["upload_id"]}/archive/{entry["entry_id"]}#/data'
                for entry in results.data
            ]
        except Exception as exc:
            logger.info(
                'onboarding entry lookup skipped',
                member_email=self.email,
                reason=str(exc),
            )
            return []

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        super().normalize(archive, logger)

        # Link all onboarding questionnaires of this member (matched via the
        # Keycloak user_id behind the member email).  Manually added
        # references are kept; discovered ones are merged in.
        existing = {
            getattr(ref, 'm_proxy_value', None)
            for ref in (self.onboarding_entries or [])
        }
        discovered = [
            url
            for url in self._find_onboarding_entries(archive, logger)
            if url not in existing
        ]
        if discovered:
            self.onboarding_entries = list(self.onboarding_entries or []) + discovered

        # Mirror list quantities into the hidden *_terms subsections so the
        # app can search and display them via a scalar `value` path.
        self.expertise_terms = [
            ExpertiseTerm(value=v) for v in _unique_clean(self.expertise)
        ]
        self.mailing_list_terms = [
            MailingListTerm(value=v) for v in _unique_clean(self.mailing_lists)
        ]

        # Derive the entry name from the person's name so it stays meaningful
        # regardless of how the entry was created or edited.  Without this, a
        # GUI edit + save drops the file-provided entry_name and NOMAD falls
        # back to the raw mainfile name (e.g. 'member_Last_First.archive.json').
        display_name = ' '.join(
            part for part in (self.first_name, self.last_name) if part
        ).strip()
        if display_name and archive.metadata is not None:
            archive.metadata.entry_name = display_name


m_package.__init_metainfo__()
