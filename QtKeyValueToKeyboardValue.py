modifiers = {
    'ctrl': 16777249,
    'left windows': 16777250,
    'alt': 16777251,
    'shift': 16777248,
    'end': 16777233,
    'home': 16777232,
    'esc': 16777216,
    'del': 16777223,
    'backspace': 16777219,
    'left': 16777234,
    'up': 16777235,
    'right': 16777236,
    'down': 16777237,
    'page down': 16777239,
    'page up': 16777238,
    'f1': 16777264,
    'f2': 16777265,
    'f3': 16777266,
    'f4': 16777267,
    'f5': 16777268,
    'f6': 16777269,
    'f7': 16777270,
    'f8': 16777271,
    'f9': 16777272,
    'f10': 16777273,
    'f11': 16777274,
    'f12': 16777275
}


def qt_to_keyboard(qtval):
    key_list = list(modifiers.keys())
    return key_list.index(qtval)
