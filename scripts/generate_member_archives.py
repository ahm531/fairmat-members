#!/usr/bin/env python3
"""Generate individual Person ``*.archive.json`` files from the members CSV.

This replaces the former NOMAD parser: instead of parsing the spreadsheet
inside NOMAD, this script is run locally and the resulting archive files are
uploaded to the oasis, where NOMAD's built-in archive parser turns each file
into an editable Person entry.

The Person sections are built with the plugin's own schema classes, so all
controlled vocabularies (member type, areas, mailing lists, ...) are
validated while generating.  Rows that fail validation are reported and
skipped, never written.

Usage (from the repository root, inside the distro environment)::

    uv run python scripts/generate_member_archives.py
    uv run python scripts/generate_member_archives.py local/members.csv -o local/archives_20260717

Input and output live under ``local/`` on purpose: the roster contains
personal data and ``local/`` is git-ignored in this public repository.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import date
from pathlib import Path

from nomad.datamodel import EntryArchive, EntryMetadata

from fairmat_members.schema_packages.schema_package import (
    Affiliation,
    EventInvitation,
    ExternalProject,
    FAIRmatRoleAssignment,
    Person,
)

REPO_ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Column names (CSV header row)
# ---------------------------------------------------------------------------

COL_LAST_NAME = 'Last Name'
COL_FIRST_NAME = 'First Name'
COL_EMAIL = 'Email'
COL_AFFILIATION = 'Affiliation'
COL_AFFILIATION_ROR = 'Affiliation ROR'
COL_CITY = 'City'
COL_COUNTRY = 'Country'
COL_MEMBER_TYPE = 'Type'
COL_AREA_LEADER = 'Area Leader'
COL_DEPUTY_AL = 'Deputy Area Leader'
COL_TASK_LEADER = 'Task Leader'
COL_PARTICIPANT = 'Participant'
COL_MEMBER = 'Member'
COL_NOTES = 'Comment'
COL_INVITE_MEETING = 'Invitation to project meeting'
COL_INVITE_RETREAT = 'Invitation to the retreat'
COL_REIMBURSEMENT = 'Reimbursement'
COL_MAIN_MAIL = 'Main Mail'
COL_ORCID = 'ORCID'
COL_EXTERNAL_PROJECTS = 'External projects'

# ---------------------------------------------------------------------------
# Controlled vocabulary maps (lower-case key -> canonical value)
# ---------------------------------------------------------------------------

MEMBER_TYPE_MAP = {
    'pi': 'PI',
    'pi deputy': 'External',
    'coworker': 'Coworker',
    'coordinator': 'Coordinator',
    'external': 'External',
    'alumni': 'Alumni',
    'collaborator': 'Collaborator',
}

AREA_MAP = {
    'a': 'Area A', 'b': 'Area B', 'c': 'Area C', 'd': 'Area D',
    'e': 'Area E', 'f': 'Area F', 'g': 'Area G', 'h': 'Area H',
    'area a': 'Area A', 'area b': 'Area B', 'area c': 'Area C',
    'area d': 'Area D', 'area e': 'Area E', 'area f': 'Area F',
    'area g': 'Area G', 'area h': 'Area H',
}

MAIN_MAIL_MAP = {
    'pi': 'fairmat2-pi@listen.physik.hu-berlin.de',
    'coworker': 'fairmat-coworkers@listen.physik.hu-berlin.de',
    'coordinator': 'fairmat-coordinators@listen.physik.hu-berlin.de',
    'team': 'fairmat-team@listen.physik.hu-berlin.de',
    'hq': 'fairmat-hq@listen.physik.hu-berlin.de',
}

REIMB_MAP = {
    'all events': 'All events',
    'requires approval': 'Requires approval',
    'no': 'No',
}


# ---------------------------------------------------------------------------
# Cell parsing helpers
# ---------------------------------------------------------------------------


def clean(value) -> str:
    if value is None:
        return ''
    s = re.sub(r'\s+', ' ', str(value).replace('\r', ' ').strip())
    return '' if s.lower() in ('nan', 'none') else s


def extract_area(raw: str) -> str | None:
    """'G', 'G1', 'Area G' -> 'Area G'."""
    s = raw.strip()
    if not s:
        return None
    exact = AREA_MAP.get(s.lower())
    if exact:
        return exact
    return AREA_MAP.get(s[0].lower())


def split_multi(raw: str) -> list[str]:
    return [p.strip() for p in re.split(r'[,;\n|]+', raw) if p.strip()]


def parse_invited_to(meet_raw: str, retreat_raw: str) -> str | None:
    meet = meet_raw.strip().lower() == 'yes'
    retreat = retreat_raw.strip().lower() == 'yes'
    if meet and retreat:
        return 'Both'
    if meet:
        return 'Project Meeting'
    if retreat:
        return 'Users Meeting'
    return None


# ---------------------------------------------------------------------------
# Row -> Person
# ---------------------------------------------------------------------------


def build_person(row: dict, warnings: list[str]) -> tuple[Person, str]:  # noqa: PLR0912
    """Build a validated Person from one CSV row.

    Returns (person, entry_name).  Appends non-fatal issues to `warnings`.
    Raises on schema validation errors (invalid enum values etc.).
    """
    get = lambda col: clean(row.get(col, ''))  # noqa: E731

    first_name = get(COL_FIRST_NAME)
    last_name = get(COL_LAST_NAME)
    who = f'{first_name} {last_name}'.strip()

    member_type = None
    mtype_raw = get(COL_MEMBER_TYPE)
    if mtype_raw:
        member_type = MEMBER_TYPE_MAP.get(mtype_raw.lower())
        if member_type is None:
            warnings.append(f'{who}: unmapped member type {mtype_raw!r}')

    affiliations = []
    if any(get(c) for c in (COL_AFFILIATION, COL_AFFILIATION_ROR, COL_CITY, COL_COUNTRY)):
        affiliations = [
            Affiliation(
                institution_name=get(COL_AFFILIATION) or None,
                ror_id=get(COL_AFFILIATION_ROR) or None,
                city=get(COL_CITY) or None,
                country=get(COL_COUNTRY) or None,
            )
        ]

    fairmat_roles = []
    if get(COL_AREA_LEADER):
        fairmat_roles.append(
            FAIRmatRoleAssignment(role='Area Leader', area=extract_area(get(COL_AREA_LEADER)))
        )
    if get(COL_DEPUTY_AL):
        fairmat_roles.append(
            FAIRmatRoleAssignment(role='Deputy Area Leader', area=extract_area(get(COL_DEPUTY_AL)))
        )
    if get(COL_TASK_LEADER):
        task = get(COL_TASK_LEADER)
        fairmat_roles.append(
            FAIRmatRoleAssignment(role='Task Leader', task=task, area=extract_area(task))
        )
    for task in split_multi(get(COL_PARTICIPANT)):
        fairmat_roles.append(
            FAIRmatRoleAssignment(role='Participant', task=task, area=extract_area(task))
        )
    for area_raw in split_multi(get(COL_MEMBER)):
        area = extract_area(area_raw)
        if area:
            fairmat_roles.append(FAIRmatRoleAssignment(role='Member', area=area))
        else:
            warnings.append(f'{who}: unmapped member area {area_raw!r}')

    mailing_lists = []
    main_mail_raw = get(COL_MAIN_MAIL)
    if main_mail_raw:
        canonical = MAIN_MAIL_MAP.get(main_mail_raw.lower())
        if canonical:
            mailing_lists = [canonical]
        else:
            warnings.append(f'{who}: unmapped Main Mail {main_mail_raw!r}')

    event_invitation = None
    invited = parse_invited_to(get(COL_INVITE_MEETING), get(COL_INVITE_RETREAT))
    reimb_raw = get(COL_REIMBURSEMENT)
    reimb = REIMB_MAP.get(reimb_raw.lower()) if reimb_raw else None
    if reimb_raw and reimb is None:
        warnings.append(f'{who}: unmapped reimbursement {reimb_raw!r}')
    if invited or reimb:
        event_invitation = EventInvitation(invited_to=invited, reimbursement=reimb)

    external_projects = [
        ExternalProject(project_name=name)
        for name in split_multi(get(COL_EXTERNAL_PROJECTS))
    ]

    person = Person(
        first_name=first_name or None,
        last_name=last_name or None,
        email=get(COL_EMAIL) or None,
        orcid=get(COL_ORCID) or None,
        member_type=member_type,
        notes=get(COL_NOTES) or None,
        affiliations=affiliations,
        fairmat_roles=fairmat_roles,
        mailing_lists=mailing_lists or None,
        event_invitation=event_invitation,
        external_projects=external_projects,
    )
    return person, who or 'FAIRmat member'


def child_filename(first_name: str, last_name: str, idx: int, used: set[str]) -> str:
    safe_last = re.sub(r'[^\w]', '_', last_name or '')[:30]
    safe_first = re.sub(r'[^\w]', '_', first_name or '')[:20]
    base = f'member_{safe_last}_{safe_first}'.strip('_') or f'member_{idx}'
    filename = f'{base}.archive.json'
    if filename in used:
        filename = f'{base}_{idx}.archive.json'
    used.add(filename)
    return filename


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def read_csv_text(path: str) -> str:
    """Read the CSV trying UTF-8 (with/without BOM) first, then Latin-1."""
    raw = Path(path).read_bytes()
    for enc in ('utf-8-sig', 'utf-8', 'latin-1'):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    raise ValueError(f'Cannot decode {path} with any supported encoding')


def main() -> int:
    argparser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    argparser.add_argument(
        'csv_file',
        nargs='?',
        default=str(REPO_ROOT / 'local' / 'members.csv'),
        help='input members CSV (default: local/members.csv)',
    )
    argparser.add_argument(
        '-o',
        '--output',
        default=str(
            REPO_ROOT / 'local' / f'archives_{date.today().strftime("%Y%m%d")}'
        ),
        help='output directory (default: local/archives_<today>)',
    )
    args = argparser.parse_args()

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    created, skipped, errors = 0, 0, 0
    warnings: list[str] = []
    used_filenames: set[str] = set()

    csv_text = read_csv_text(args.csv_file)
    for idx, raw_row in enumerate(csv.DictReader(csv_text.splitlines()), start=1):
        row = {clean(k): v for k, v in raw_row.items() if k}
        if not (clean(row.get(COL_LAST_NAME)) or clean(row.get(COL_FIRST_NAME))):
            skipped += 1
            continue
        try:
            person, entry_name = build_person(row, warnings)
        except Exception as exc:
            errors += 1
            who = f'{clean(row.get(COL_FIRST_NAME))} {clean(row.get(COL_LAST_NAME))}'
            print(f'ERROR row {idx} ({who.strip()}): {exc}', file=sys.stderr)
            continue

        archive = EntryArchive(
            data=person, metadata=EntryMetadata(entry_name=entry_name)
        )
        filename = child_filename(
            person.first_name or '', person.last_name or '', idx, used_filenames
        )
        with open(out_dir / filename, 'w', encoding='utf-8') as out:
            json.dump(archive.m_to_dict(), out, indent=2, ensure_ascii=False)
        created += 1

    for w in warnings:
        print(f'WARNING {w}', file=sys.stderr)

    print(
        f'{created} archive files written to {out_dir} '
        f'({skipped} empty rows skipped, {errors} rows failed, '
        f'{len(warnings)} warnings)'
    )
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
