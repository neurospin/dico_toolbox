
import unittest
from dico_toolbox.database import create_test_database, extend_templates
import os.path as op


class TestDatabaseUtils(unittest.TestCase):

    def test_extend_templates(self):
        fpaths = extend_templates(
            "[center]/[subject]/t1mri/[acq]/[ana]/folds/[version]/[session]/[hemi][subject]_[session].arg",
            default_value="*",
            subject="sub-01", session="session_manual", hemi=["L", "R"])

        assert len(fpaths) == 2
        assert fpaths[0] == "*/sub-01/t1mri/*/*/folds/*/session_manual/Lsub-01_session_manual.arg"
        assert fpaths[1] == "*/sub-01/t1mri/*/*/folds/*/session_manual/Rsub-01_session_manual.arg"


class TestDatabaseMethods(unittest.TestCase):

    def test_database(self):
        db = create_test_database()
        assert len(db.list_all('subject')) == 2
        assert len(db.get(subject='001')) == 28

    def test_database_with_templates(self):
        db = create_test_database(use_template=True)
        fpaths = db.get_from_template(
            "[center]/[subject]/t1mri/[acq]/[ana]/folds/[version]/[session]/[hemi][subject]_[session].arg",
            subject=['001'], version='3.3', session="session1_manual", hemi=["L", "R"])

        assert len(fpaths) == 2


if __name__ == '__main__':
    unittest.main()
