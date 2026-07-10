from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nomad.datamodel.datamodel import EntryArchive
    from structlog.stdlib import BoundLogger

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

MAILING_LIST_VOCAB = MEnum(
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
)

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
# Sub-sections
# ---------------------------------------------------------------------------


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
            'hide': ['lab_id'],
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

    onboarding_entry = Quantity(
        type=ArchiveSection,
        label='Onboarding entry',
        description=(
            'Reference to the PI onboarding questionnaire entry in NOMAD. '
            'Applicable for PI members only.'
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
        type=MAILING_LIST_VOCAB,
        shape=['*'],
        label='Mailing lists',
        description='FAIRmat mailing lists this member is subscribed to. Multiple selections allowed.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.AutocompleteEditQuantity),
    )

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

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        super().normalize(archive, logger)

        # Derive the entry name from the person's name so it stays meaningful
        # regardless of how the entry was created or edited.  Without this, a
        # GUI edit + save drops the parser-provided entry_name and NOMAD falls
        # back to the raw mainfile name (e.g. 'member_Last_First.archive.yaml').
        display_name = ' '.join(
            part for part in (self.first_name, self.last_name) if part
        ).strip()
        if display_name and archive.metadata is not None:
            archive.metadata.entry_name = display_name


# ---------------------------------------------------------------------------
# Container schemas produced by parsers
# ---------------------------------------------------------------------------


class MemberRecord(ArchiveSection):
    """A single member record used inside FAIRmatMembersFile (parsed from a spreadsheet)."""

    m_def = Section(label_quantity='last_name')

    first_name = Quantity(type=str, label='First name')
    last_name = Quantity(type=str, label='Last name')
    email = Quantity(type=str, label='Email')
    orcid = Quantity(type=str, label='ORCID')
    institution_name = Quantity(type=str, label='Institution name')
    role = Quantity(type=FAIRMAT_ROLE_VOCAB, label='Role')
    area = Quantity(type=FAIRMAT_AREA, label='Area')
    mailing_lists = Quantity(type=MAILING_LIST_VOCAB, shape=['*'], label='Mailing lists')
    notes = Quantity(type=str, label='Notes')


class FAIRmatMembersFile(Schema):
    """Container schema produced by the members spreadsheet parser."""

    m_def = Section(
        label='FAIRmat Members File',
        categories=[UseCaseElnCategory],
    )

    members = SubSection(
        section_def=MemberRecord,
        label='Members',
        repeats=True,
    )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        super().normalize(archive, logger)


m_package.__init_metainfo__()
