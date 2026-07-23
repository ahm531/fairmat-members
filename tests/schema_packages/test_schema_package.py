import os.path

from nomad.client import normalize_all, parse


def test_schema_package():
    test_file = os.path.join('tests', 'data', 'test.archive.yaml')
    entry_archive = parse(test_file)[0]
    normalize_all(entry_archive)

    data = entry_archive.data
    assert data.first_name == 'Jane'
    assert data.last_name == 'Doe'
    assert data.area == 'Area A - Synthesis'
    assert data.member_type == 'PI'
    assert data.affiliations[0].institution_name == 'HU Berlin'
    assert data.fairmat_roles[1].role == 'Area Leader'
    assert data.fairmat_roles[1].area == 'Area A - Synthesis'
    assert data.fairmat_roles[1].task == 'Task A1 – Synthesis Methods'

    # normalize() expands bare ORCID / ROR ids into full URLs so the launch
    # button works and the stored value shows the full address
    assert data.orcid == 'https://orcid.org/0009-0002-0896-320X'
    assert data.affiliations[0].ror_id == 'https://ror.org/01hcx6992'

    # normalize() derives the entry name from the person's name
    assert entry_archive.metadata.entry_name == 'Jane Doe'

    # normalize() mirrors the list quantities into the hidden, searchable
    # *_terms subsections used by the app
    assert [t.value for t in data.expertise_terms] == ['NeXus', 'FAIR data']
    assert [t.value for t in data.mailing_list_terms] == [
        'fairmat-coordinators@listen.physik.hu-berlin.de'
    ]

    # normalize() mirrors the distinct roles into fairmat_role_terms,
    # deduplicated (two 'Participant' roles collapse to one) and ordered with
    # leadership roles first, then Participant/Member
    assert [t.value for t in data.fairmat_role_terms] == [
        'Area Leader',
        'Participant',
    ]

    # normalize() builds a read-only rich-text overview summary with the key
    # member information, as a nested bulleted (<ul>/<li>) structure
    assert data.summary
    assert '<b>Jane Doe</b>' in data.summary
    assert 'jane.doe@example.com' in data.summary
    assert 'Area A - Synthesis' in data.summary
    assert 'Area Leader' in data.summary
    # nested list structure and grouped sections
    assert '<ul>' in data.summary and '<li>' in data.summary
    # the test entry has an Area Leader role -> a Leadership roles group
    assert '<b>Leadership roles</b>' in data.summary
    assert '<b>Affiliations</b>' in data.summary
    assert '<b>Mailing lists</b>' in data.summary
    # header stat line
    assert 'role(s)' in data.summary
