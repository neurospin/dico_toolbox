
import unittest
from dico_toolbox.database import create_test_database, extend_templates
import os.path as op


class TestDatabaseMethods(unittest.TestCase):

    def test_database(self):
        db = create_test_database()

        print(db.list_all('subject'))
        assert len(db.list_all('subject')) == 2
        assert len(db.get(subject='001')) == 17
        assert len(db.get(subject='002')) == 9

    def test_extend_templates(self):
        fpaths = extend_templates(
            "[center]/[subject]/t1mri/[acq]/[ana]/folds/[version]/[session]/[hemi][session]_[subject].arg",
            default_value="*",
            subject="sub-01", session="session_manual", hemi=["L", "R"])

        print(fpaths)
        assert len(fpaths) == 2
        assert fpaths[0] == "*/sub-01/t1mri/*/*/folds/*/session_manual/Lsession_manual_sub-01.arg"
        assert fpaths[1] == "*/sub-01/t1mri/*/*/folds/*/session_manual/Rsession_manual_sub-01.arg"


if __name__ == '__main__':
    unittest.main()
