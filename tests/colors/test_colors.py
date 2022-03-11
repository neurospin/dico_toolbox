import pytest


from dico_toolbox.anatomist.colors import *


def test_parse_color_argument():
    assert parse_color_argument(
        dict(r=0, g=0, b=0, a=0)) == dict(r=0, g=0, b=0, a=0)
    assert parse_color_argument([0, 0, 0]) == dict(r=0, g=0, b=0)
    assert parse_color_argument([0, 0, 0, 0]) == dict(r=0, g=0, b=0, a=0)
    assert parse_color_argument('red') == dict(
        zip('rgb', color_values.colors['red']))
    with pytest.raises(TypeError):
        parse_color_argument(1)


def test_check_color_dict():
    with pytest.raises(KeyError):
        check_color_dict(dict(m="a"))
    with pytest.raises(ValueError):
        check_color_dict(dict(r="a"))
