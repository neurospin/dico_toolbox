
import dico_toolbox as dtb
import os.path as op


def test_database():
    db = dtb.database.create_test_database()

    assert len(db.list_all('subject')) == 2
    assert len(db.get(subject='001')) == 17
    assert len(db.get(subject='002')) == 9
