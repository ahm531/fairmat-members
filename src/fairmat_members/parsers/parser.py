"""
Parser for FAIRmat member directory files (Excel or CSV).

Expected CSV column headers (new format)
-----------------------------------------
  Last Name                     – A: last_name
  First Name                    – B: first_name
  Email                         – C: email
  Affiliation                   – D: institution_name  (Affiliation sub-section)
  Affiliation ROR               – E: ror_id            (Affiliation sub-section)
  City                          – F: city              (Affiliation sub-section)
  Country                       – G: country           (Affiliation sub-section)
  Type                          – H: member_type (PI / Coworker / Coordinator / External / Alumni)
  Area Leader                   – I: FAIRmatRoleAssignment(role='Area Leader',        area=<value>)
  Deputy Area Leader            – J: FAIRmatRoleAssignment(role='Deputy Area Leader', area=<value>)
  Task Leader                   – K: FAIRmatRoleAssignment(role='Task Leader', task=<value>, area=<extracted>)
  Participant                   – L: one subsection per comma-separated task  (role='Participant')
  Member                        – M: one subsection per comma-separated area  (role='Member')
  Comment                       – N: notes
  Invitation to project meeting – O: used to derive invited_to
  Invitation to the retreat     – P: used to derive invited_to
  Reimbursement                 – Q: reimbursement status
  Main Mail                     – T: primary mailing list indicator
  ORCID                         – U: orcid

Each non-empty row (with at least a first or last name) creates one individual
``Person`` child archive entry (``member_<Last>_<First>.archive.json``).
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import TYPE_CHECKING

from nomad.datamodel import EntryArchive as EA
from nomad.datamodel import EntryMetadata
from nomad.parsing.parser import MatchingParser

from fairmat_members.schema_packages.schema_package import (
    Affiliation,
    EventInvitation,
    FAIRmatMembersFile,
    FAIRmatRoleAssignment,
    MemberRecord,
    Person,
)

if TYPE_CHECKING:
    from nomad.datamodel.datamodel import EntryArchive
    from structlog.stdlib import BoundLogger

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Column names  (CSV / Excel header row)
# ---------------------------------------------------------------------------

_COL_LAST_NAME       = 'Last Name'
_COL_FIRST_NAME      = 'First Name'
_COL_EMAIL           = 'Email'
_COL_AFFILIATION     = 'Affiliation'
_COL_AFFILIATION_ROR = 'Affiliation ROR'
_COL_CITY            = 'City'
_COL_COUNTRY         = 'Country'
_COL_MEMBER_TYPE     = 'Type'
_COL_AREA_LEADER     = 'Area Leader'
_COL_DEPUTY_AL       = 'Deputy Area Leader'
_COL_TASK_LEADER     = 'Task Leader'
_COL_PARTICIPANT     = 'Participant'
_COL_MEMBER          = 'Member'
_COL_NOTES           = 'Comment'
_COL_INVITE_MEETING  = 'Invitation to project meeting'
_COL_INVITE_RETREAT  = 'Invitation to the retreat'
_COL_REIMBURSEMENT   = 'Reimbursement'
_COL_MAIN_MAIL       = 'Main Mail'
_COL_ORCID           = 'ORCID'

# ---------------------------------------------------------------------------
# Controlled vocabulary maps  (lower-case key → canonical value)
# ---------------------------------------------------------------------------

_MEMBER_TYPE_MAP: dict[str, str] = {
    'pi': 'PI',
    'pi deputy': 'External',
    'coworker': 'Coworker',
    'coordinator': 'Coordinator',
    'external': 'External',
    'alumni': 'Alumni',
    'collaborator': 'Collaborator',
}

_AREA_MAP: dict[str, str] = {
    'a': 'Area A', 'b': 'Area B', 'c': 'Area C', 'd': 'Area D',
    'e': 'Area E', 'f': 'Area F', 'g': 'Area G', 'h': 'Area H',
    'area a': 'Area A', 'area b': 'Area B', 'area c': 'Area C',
    'area d': 'Area D', 'area e': 'Area E', 'area f': 'Area F',
    'area g': 'Area G', 'area h': 'Area H',
}

_MAIN_MAIL_MAP: dict[str, str] = {
    'pi': 'fairmat2-pi@listen.physik.hu-berlin.de',
    'coworker': 'fairmat-coworkers@listen.physik.hu-berlin.de',
    'coordinator': 'fairmat-coordinators@listen.physik.hu-berlin.de',
    'team': 'fairmat-team@listen.physik.hu-berlin.de',
    'hq': 'fairmat-hq@listen.physik.hu-berlin.de',
}

_REIMB_MAP: dict[str, str] = {
    'all events': 'All events',
    'requires approval': 'Requires approval',
    'no': 'No',
}

_MAILING_LOWER: dict[str, str] = {
    m.lower(): m for m in [
        'fairmat-area-leaders@listen.physik.hu-berlin.de',
        'fairmat-coordinators@listen.physik.hu-berlin.de',
        'fairmat-coworkers@listen.physik.hu-berlin.de',
        'fairmat-hq@listen.physik.hu-berlin.de',
        'fairmat-team@listen.physik.hu-berlin.de',
        'fairmat2-area-a@listen.physik.hu-berlin.de',
        'fairmat2-area-b@listen.physik.hu-berlin.de',
        'fairmat2-area-c@listen.physik.hu-berlin.de',
        'fairmat2-area-d@listen.physik.hu-berlin.de',
        'fairmat2-area-e@listen.physik.hu-berlin.de',
        'fairmat2-area-f@listen.physik.hu-berlin.de',
        'fairmat2-area-g@listen.physik.hu-berlin.de',
        'fairmat2-pi@listen.physik.hu-berlin.de',
    ]
}

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def _clean(value) -> str:
    """Return a whitespace-normalised, non-nan string."""
    if value is None:
        return ''
    s = re.sub(r'\s+', ' ', str(value).replace('\r', ' ').strip())
    return '' if s.lower() in ('nan', 'none', '') else s


def _gcol(row, col_name: str) -> str:
    """Return cleaned cell value by column name; empty string if missing."""
    try:
        return _clean(row.get(col_name, ''))
    except (KeyError, AttributeError):
        return ''


def _parse_member_type(raw: str) -> str | None:
    """Map the Type column value to a MEMBER_TYPE canonical string."""
    if not raw:
        return None
    return _MEMBER_TYPE_MAP.get(raw.strip().lower())


def _extract_area(raw: str) -> str | None:
    """
    Extract a canonical 'Area X' string from a raw value.
    Handles single letters ('G'), task codes ('G1', 'B3'), or 'Area X' strings.
    """
    if not raw:
        return None
    s = raw.strip()
    if not s:
        return None
    # Try exact match first (handles 'Area A', 'area g', single letters, etc.)
    exact = _AREA_MAP.get(s.lower())
    if exact:
        return exact
    # Fall back to first character for task codes like 'G1', 'B3', 'D2'
    return _AREA_MAP.get(s[0].lower())


def _split_csv(raw: str) -> list[str]:
    """Split a comma-separated cell into cleaned non-empty parts."""
    if not raw:
        return []
    return [p.strip() for p in raw.split(',') if p.strip()]


def _parse_main_mail(raw: str) -> str | None:
    """Map the 'Main Mail' column indicator to a canonical mailing-list address."""
    if not raw:
        return None
    return _MAIN_MAIL_MAP.get(raw.strip().lower())


def _parse_invited_to(meet_raw: str, retreat_raw: str) -> str | None:
    """Derive the INVITED_TO value from the two invitation columns."""
    meet    = meet_raw.strip().lower() == 'yes'
    retreat = retreat_raw.strip().lower() == 'yes'
    if meet and retreat:
        return 'Both'
    if meet:
        return 'Project Meeting'
    if retreat:
        return 'Users Meeting'
    return None


def _parse_reimbursement(raw: str) -> str | None:
    """Map the Reimbursement column value to the canonical schema string."""
    if not raw:
        return None
    return _REIMB_MAP.get(raw.strip().lower())


def _parse_mailing_lists(raw: str) -> list[str]:
    """Split a mailing-list cell and return only recognised addresses."""
    if not raw:
        return []
    parts = re.split(r'[,;\n|]+', raw)
    result = []
    seen: set[str] = set()
    for part in parts:
        s = part.strip().lower()
        if not s:
            continue
        canonical = _MAILING_LOWER.get(s)
        if canonical and canonical not in seen:
            result.append(canonical)
            seen.add(canonical)
    return result


# ---------------------------------------------------------------------------
# DataFrame loader  (CSV with header=0, or Excel with 4 metadata rows skipped)
# ---------------------------------------------------------------------------


def _load_dataframe(mainfile: str):
    import pandas as pd
    if mainfile.lower().endswith(('.xlsx', '.xls')):
        # Legacy Excel format: rows 1-4 are metadata, row 5 is the header
        return pd.read_excel(mainfile, header=0, skiprows=4, dtype=str)
    # CSV: single header row
    for enc in ('utf-8-sig', 'utf-8', 'latin-1'):
        try:
            return pd.read_csv(
                mainfile, header=0, dtype=str, encoding=enc,
                skip_blank_lines=True,
            )
        except UnicodeDecodeError:
            continue
    raise ValueError(f'Cannot decode {mainfile} with any supported encoding')


def _prepare_dataframe(mainfile: str):
    """Load and normalise the member spreadsheet into a DataFrame.

    Drops fully-empty rows and strips surrounding whitespace from column
    names.  Returns the DataFrame; raising on unreadable files is left to the
    caller.
    """
    df = _load_dataframe(mainfile)
    df = df.dropna(how='all')
    df.columns = [str(c).strip() for c in df.columns]
    return df


def _row_has_name(row) -> bool:
    """A row is a member row iff it carries at least a first or last name."""
    return bool(_gcol(row, _COL_LAST_NAME) or _gcol(row, _COL_FIRST_NAME))


def _build_person_and_record(row):
    """Build a ``(Person, MemberRecord, entry_name)`` tuple from one row.

    Assumes the row has already passed ``_row_has_name``.  Kept free of any
    archive/context side effects so it can be reused by both mainfile-key
    generation and the actual parse.
    """
    last_name  = _gcol(row, _COL_LAST_NAME)
    first_name = _gcol(row, _COL_FIRST_NAME)

    email        = _gcol(row, _COL_EMAIL)
    affil_raw    = _gcol(row, _COL_AFFILIATION)
    ror_raw      = _gcol(row, _COL_AFFILIATION_ROR)
    city_raw     = _gcol(row, _COL_CITY)
    country_raw  = _gcol(row, _COL_COUNTRY)
    mtype_raw    = _gcol(row, _COL_MEMBER_TYPE)
    area_ldr_raw = _gcol(row, _COL_AREA_LEADER)
    dep_al_raw   = _gcol(row, _COL_DEPUTY_AL)
    task_ldr_raw = _gcol(row, _COL_TASK_LEADER)
    part_raw     = _gcol(row, _COL_PARTICIPANT)
    member_raw   = _gcol(row, _COL_MEMBER)
    notes        = _gcol(row, _COL_NOTES)
    meet_raw     = _gcol(row, _COL_INVITE_MEETING)
    retreat_raw  = _gcol(row, _COL_INVITE_RETREAT)
    reimb_raw    = _gcol(row, _COL_REIMBURSEMENT)
    main_mail    = _gcol(row, _COL_MAIN_MAIL)
    orcid        = _gcol(row, _COL_ORCID)

    # -- Affiliation (cols D, E, F, G) ----------------------------------
    affiliations = []
    if affil_raw or ror_raw or city_raw or country_raw:
        affiliations = [Affiliation(
            institution_name=affil_raw or None,
            ror_id=ror_raw or None,
            city=city_raw or None,
            country=country_raw or None,
        )]

    # -- Member type (col H) --------------------------------------------
    member_type = _parse_member_type(mtype_raw)

    # -- FAIRmat roles (cols I–M) ----------------------------------------
    fairmat_roles = []

    # Col I: Area Leader
    if area_ldr_raw:
        fairmat_roles.append(FAIRmatRoleAssignment(
            role='Area Leader',
            area=_extract_area(area_ldr_raw),
        ))

    # Col J: Deputy Area Leader
    if dep_al_raw:
        fairmat_roles.append(FAIRmatRoleAssignment(
            role='Deputy Area Leader',
            area=_extract_area(dep_al_raw),
        ))

    # Col K: Task Leader (single task; area extracted from task code)
    if task_ldr_raw:
        fairmat_roles.append(FAIRmatRoleAssignment(
            role='Task Leader',
            task=task_ldr_raw,
            area=_extract_area(task_ldr_raw),
        ))

    # Col L: Participant (comma-separated tasks; one subsection each)
    for task in _split_csv(part_raw):
        fairmat_roles.append(FAIRmatRoleAssignment(
            role='Participant',
            task=task,
            area=_extract_area(task),
        ))

    # Col M: Member (comma-separated area codes; one subsection each)
    for area_raw in _split_csv(member_raw):
        area = _extract_area(area_raw)
        if area:
            fairmat_roles.append(FAIRmatRoleAssignment(
                role='Member',
                area=area,
            ))

    # -- Primary mailing list from 'Main Mail' column (col T) -----------
    mailing_lists = []
    canonical_mail = _parse_main_mail(main_mail)
    if canonical_mail:
        mailing_lists = [canonical_mail]

    # -- Event invitation & reimbursement -------------------------------
    invited = _parse_invited_to(meet_raw, retreat_raw)
    reimb   = _parse_reimbursement(reimb_raw)
    event_invitation = None
    if invited or reimb:
        event_invitation = EventInvitation(
            invited_to=invited,
            reimbursement=reimb,
        )

    person = Person(
        first_name=first_name or None,
        last_name=last_name or None,
        email=email or None,
        orcid=orcid or None,
        member_type=member_type,
        notes=notes or None,
        affiliations=affiliations,
        fairmat_roles=fairmat_roles,
        mailing_lists=mailing_lists if mailing_lists else None,
        event_invitation=event_invitation,
    )

    first_role = fairmat_roles[0] if fairmat_roles else None
    record = MemberRecord(
        first_name=first_name or None,
        last_name=last_name or None,
        email=email or None,
        orcid=orcid or None,
        institution_name=affil_raw or None,
        role=first_role.role if first_role else None,
        area=first_role.area if first_role else None,
        mailing_lists=mailing_lists if mailing_lists else None,
        notes=notes or None,
    )

    entry_name = f'{first_name} {last_name}'.strip() or 'FAIRmat member'
    return person, record, entry_name


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


class FAIRmatMembersParser(MatchingParser):
    """
    Parses a FAIRmat member directory Excel or CSV file.

    The spreadsheet (the *mainfile*) becomes a ``FAIRmatMembersFile`` summary
    entry.  In addition, each row that contains at least a first or last name is
    written out as its own ``member_<Last>_<First>.archive.json`` raw file
    holding a ``Person``.  Those files are then processed by NOMAD's built-in
    archive parser, producing individual, editable ``Person`` entries that can
    each be downloaded as a single ``.archive.json`` file.

    Guard against self-matching
    ---------------------------
    The generated ``*.archive.json`` files must be picked up by the archive
    parser, NOT by this parser again.  During matching, plugin parsers are
    checked before the archive parser, so ``is_mainfile`` is overridden to
    explicitly refuse any ``.archive.(yaml|yml|json)`` file.  Without this guard
    a generated child could be re-matched here and overwritten with an empty
    ``FAIRmatMembersFile``, which previously made the entries render blank.
    """

    # Files this parser must never claim (they belong to the archive parser).
    _ARCHIVE_SUFFIX_RE = re.compile(r'(?i)\.archive\.(ya?ml|json)$')

    def is_mainfile(
        self,
        filename: str,
        mime: str,
        buffer: bytes,
        decoded_buffer: str,
        compression: str | None = None,
    ):
        # Never claim archive files – those are the children we generate.
        if self._ARCHIVE_SUFFIX_RE.search(filename):
            return False
        return super().is_mainfile(
            filename, mime, buffer, decoded_buffer, compression
        )

    def parse(
        self,
        mainfile: str,
        archive: EntryArchive,
        logger: BoundLogger,
        child_archives: dict[str, EntryArchive] = None,
    ) -> None:
        file_size = os.path.getsize(mainfile) if os.path.exists(mainfile) else -1
        is_excel  = mainfile.lower().endswith(('.xlsx', '.xls'))
        file_type = 'Excel' if is_excel else 'CSV'
        logger.info(
            'FAIRmatMembersParser.parse',
            mainfile=mainfile,
            size_bytes=file_size,
            file_type=file_type,
        )

        try:
            df = _prepare_dataframe(mainfile)
        except Exception as exc:
            logger.error('Failed to load file', exc_info=exc)
            return

        logger.info('rows loaded', count=len(df), file_type=file_type)

        created = 0
        skipped = 0
        member_records = []
        used_filenames: set[str] = set()

        for idx, row in df.iterrows():
            if not _row_has_name(row):
                skipped += 1
                continue

            person, record, entry_name = _build_person_and_record(row)
            member_records.append(record)

            filename = self._child_filename(record, idx, used_filenames)
            if self._write_child(archive, filename, person, entry_name, logger):
                created += 1

        # The mainfile entry itself carries the lightweight summary.
        archive.data = FAIRmatMembersFile(members=member_records)
        logger.info(
            'FAIRmatMembersParser done',
            created=created,
            skipped=skipped,
        )

    @staticmethod
    def _child_filename(record, idx, used_filenames: set[str]) -> str:
        """Build a unique, collision-safe ``member_*.archive.json`` filename."""
        safe_last  = re.sub(r'[^\w]', '_', record.last_name or '')[:30]
        safe_first = re.sub(r'[^\w]', '_', record.first_name or '')[:20]
        base       = f'member_{safe_last}_{safe_first}'.strip('_') or f'member_{idx}'
        filename   = f'{base}.archive.json'
        if filename in used_filenames:
            filename = f'{base}_{idx}.archive.json'
        used_filenames.add(filename)
        return filename

    @staticmethod
    def _write_child(archive, filename, person, entry_name, logger) -> bool:
        """Write one Person as a raw ``.archive.json`` file and register it.

        Returns True on success.  The archive parser will subsequently turn the
        file into an individual, editable ``Person`` entry.
        """
        child = EA(
            data=person,
            m_context=archive.m_context,
            metadata=EntryMetadata(entry_name=entry_name),
        )
        try:
            # Serialise BEFORE opening the file: opening with 'w' truncates it
            # to 0 bytes, so a serialisation error must not leave an empty file.
            json_str = json.dumps(
                child.m_to_dict(),
                indent=2,
                ensure_ascii=False,
            )
        except Exception as exc:
            logger.error(
                'Failed to serialise child entry',
                file=filename, name=entry_name, exc_info=exc,
            )
            return False

        try:
            with archive.m_context.raw_file(filename, 'w') as outfile:
                outfile.write(json_str)
            archive.m_context.process_updated_raw_file(filename, allow_modify=True)
            logger.info('created member entry', file=filename, name=entry_name)
            return True
        except Exception as exc:
            logger.error(
                'Failed to write child entry',
                file=filename, name=entry_name, exc_info=exc,
            )
            return False
