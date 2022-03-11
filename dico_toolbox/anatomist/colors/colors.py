from . import color_values


def check_color_dict(color_dict):
    """The key of a color dictionnary must be one of r,g,b,a, if not raise KeyError
    The values must be numbers, if not raise ValueError"""

    valid_keys = ('r', 'g', 'b', 'a')
    for k, v in color_dict.items():
        if k not in valid_keys:
            # color contain invalid key
            raise KeyError(
                f"the keys of a color dictionnary must be r,b,g,a. got {k}:{v}")

        # color contain invalid key
        try:
            float(v)
        except:
            raise ValueError(
                f"the values of a color dictionnary must be numbers {k}:{v}")


def parse_color_argument(color):
    """Parse a string, dict or other iterable into a RGBA color dictionnary.

    - if color is a String, it must be one of the keys of mpl_colors.colors
    - if color is an iterable, it must contain only numbers
    - if color is a dict it is returned as is


    """
    d = dict()

    if isinstance(color, dict):
        # argument is a dictionnary
        check_color_dict(color)
        d = color

    elif isinstance(color, str):
        # argument is a string
        try:
            if color in color_values.color_short:
                color = color_values.color_short[color]
            rgb = color_values.colors[color]
            d = dict(zip('rgb', rgb))
        except KeyError:
            raise ValueError(
                f"{color} is an invalid color name. It must be one of {list(color_values.colors.keys())}")

    else:
        try:
            iter(color)
            d = dict(zip('rgba', color))
        except TypeError:
            raise TypeError(f"'{color}' is not a valid color.")

    return d
