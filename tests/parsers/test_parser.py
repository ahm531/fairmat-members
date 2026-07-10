"""
Basic smoke test for FAIRmatMembersParser.

The test creates a minimal in-memory CSV and runs the parser through a
ClientContext so that child-archive writes go to a temp directory rather
than the real upload store.
"""

from __future__ import annotations

import logging
import os
import tempfile

import pytest
from nomad.datamodel import EntryArchive
from nomad.datamodel.context import ClientContext

from fairmat_members.parsers.parser import FAIRmatMembersParser

# Minimal CSV that exercises all major code paths
_SAMPLE_CSV = """\
Last Name,First Name,Email,Affiliation,Affiliation ROR,City,Country,Type,Area Leader,Deputy Area Leader,Task Leader,Participant,Member,Comment,Invitation to project meeting,Invitation to the retreat,Reimbursement,,,Main Mail,ORCID
Doe,Jane,jane.doe@example.com,HU Berlin,,Berlin,Germany,PI,A,,,,,,,,,,,pi,0000-0001-2345-6789
Smith,John,john.smith@example.com,FU Berlin,,Berlin,Germany,Coworker,,,,G1,G,,yes,no,All events,,,coworker,
"""


@pytest.fixture()
def sample_csv(tmp_path):
    """Write the sample CSV to a temp file and return its path."""
    p = tmp_path / 'members.csv'
    p.write_text(_SAMPLE_CSV, encoding='utf-8')
    return str(p)


def test_parser_instantiation():
    """Parser must instantiate without arguments."""
    parser = FAIRmatMembersParser()
    assert parser is not None


def test_parse_csv(sample_csv, tmp_path):
    """Parse a minimal CSV and confirm at least one MemberRecord is produced."""
    context = ClientContext(local_dir=str(tmp_path))
    archive = EntryArchive(m_context=context)

    parser = FAIRmatMembersParser()
    parser.parse(sample_csv, archive, logging.getLogger('test'))

    assert archive.data is not None, 'archive.data should be set after parsing'
    assert len(archive.data.members) >= 1, 'at least one MemberRecord expected'


def test_mainfile_not_modified(sample_csv, tmp_path):
    """The parser must never modify the uploaded mainfile."""
    size_before = os.path.getsize(sample_csv)

    context = ClientContext(local_dir=str(tmp_path))
    archive = EntryArchive(m_context=context)
    FAIRmatMembersParser().parse(sample_csv, archive, logging.getLogger('test'))

    size_after = os.path.getsize(sample_csv)
    assert size_before == size_after, (
        f'mainfile was modified during parsing: {size_before} → {size_after} bytes'
    )
