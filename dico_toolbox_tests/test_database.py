
from dico_toolbox.database import extend_templates
from dico_toolbox import test_data


def test_extend_templates():
    fpaths = extend_templates(
        "[center]/[subject]/t1mri/[acq]/[ana]/folds/[version]/[session]/[hemi][subject]_[session].arg",
        default_value="*",
        subject="sub-01", session="session_manual", hemi=["L", "R"])

    assert len(fpaths) == 2
    assert fpaths[0] == "*/sub-01/t1mri/*/*/folds/*/session_manual/Lsub-01_session_manual.arg"
    assert fpaths[1] == "*/sub-01/t1mri/*/*/folds/*/session_manual/Rsub-01_session_manual.arg"


def test_database():
    db = test_data.bv_database()
    assert len(db.list_all('subject')) == 2
    assert len(db.get(subject='001')) == 26


def test_database_with_templates():
    db = test_data.bv_database()
    fpaths = db.get_from_template(
        "morphologist_labelled_graph",
        subject=['001'], version='3.3', session="session1_manual", hemi=["L", "R"])
    assert len(fpaths) == 2
