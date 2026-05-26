
def filter_capitalize_first(word: str):
    try:
        return word[0].upper() + word[1:]
    except IndexError:
        return word


def filter_capitalize_all(phrase: str):
    try:
        return " ".join(
            [
                word[0].upper() + word[1:] for word in phrase.split(' ')
            ]
        )
    except IndexError:
        return phrase


def filter_pluralize(noun: str):
    if noun[-1] not in ['s', 'x', 'z']:
        if noun[-1] == 'y' and noun[-2] not in ['a', 'e', 'i', 'o', 'u']:
            return noun[:-1] + "ies"
        return noun + 's'
    return noun + 'es'


def filter_simple_past(verb: str):
    if (
        verb[-1] in ['b', 'd', 'm', 'n', 'p'] and
        verb[-2] != verb[-1]
    ) or (
        verb[-1] == 'g' and
        verb[-2:-1] != "ng"
    ):
        verb += verb[-1] + "ed"
    elif verb[-1] == 'e':
        verb += 'd'
    else:
        verb += "ed"
    return verb
