
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
    if noun[-1] in ['s', 'z'] and noun[-2] != noun[-1]:
        return noun + noun[-1] + "es"
    return noun + "es"


def filter_simple_past(verb: str):
    if (
        verb[-1] in ['b', 'd', 'l', 'm', 'n', 'p', 'z'] and
        verb[-2] != verb[-1]
    ) or (
        verb[-1] == 'g' and
        verb[-2:] != "ng"
    ):
        return verb + verb[-1] + "ed"
    if verb[-1] == 'e':
        return verb + 'd'
    return verb + "ed"
