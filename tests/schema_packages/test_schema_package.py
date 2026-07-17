import os.path

from nomad.client import normalize_all, parse


def test_schema_package():
    test_file = os.path.join('tests', 'data', 'test.archive.yaml')
    entry_archive = parse(test_file)[0]
    normalize_all(entry_archive)

    data = entry_archive.data
    assert data.first_name == 'Jane'
    assert data.last_name == 'Doe'
    assert data.member_type == 'PI'
    assert data.affiliations[0].institution_name == 'HU Berlin'
    assert data.fairmat_roles[0].role == 'Area Leader'

    # normalize() derives the entry name from the person's name
    assert entry_archive.metadata.entry_name == 'Jane Doe'

    # normalize() mirrors the list quantities into the hidden, searchable
    # *_terms subsections used by the app
    assert [t.value for t in data.expertise_terms] == ['NeXus', 'FAIR data']
    assert [t.value for t in data.mailing_list_terms] == [
        'fairmat-coordinators@listen.physik.hu-berlin.de'
    ]
