import os.path

from nomad.client import normalize_all, parse


def test_schema_package():
    test_file = os.path.join('tests', 'data', 'test.archive.yaml')
    entry_archive = parse(test_file)[0]
    normalize_all(entry_archive)

    assert entry_archive.data.first_name == 'Markus'
    assert entry_archive.data.last_name == 'Scheidgen'
    # normalize() derives the entry name from first + last name.
    assert entry_archive.metadata.entry_name == 'Markus Scheidgen'
