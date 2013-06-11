from htmlentitydefs import name2codepoint
import re

from crawlmi.utils.python import to_unicode


_ent_re = re.compile(r'&(#?(x?))([^&;\s]+);')

def remove_entities(text, keep=(), remove_illegal=True, encoding='utf-8'):
    '''Remove entities from the given text by converting them to
    corresponding unicode character.

    `text` can be a unicode string or a regular string encoded in the given
    `encoding` (which defaults to 'utf-8').

    If 'keep' is passed (with a list of entity names) those entities will
    be kept (they won't be removed).

    It supports both numeric (&#nnnn; and &#hhhh;) and named (&nbsp; &gt;)
    entities.

    If remove_illegal is True, entities that can't be converted are removed.
    If remove_illegal is False, entities that can't be converted are kept "as
    is". For more information see the tests.

    Always returns a unicode string (with the entities removed).
    '''

    def convert_entity(m):
        entity_body = m.group(3)
        if m.group(1):
            try:
                if m.group(2):
                    number = int(entity_body, 16)
                else:
                    number = int(entity_body, 10)
                # Numeric character references in the 80-9F range are typically
                # interpreted by browsers as representing the characters mapped
                # to bytes 80-9F in the Windows-1252 encoding. For more info
                # see: http://en.wikipedia.org/wiki/Character_encodings_in_HTML
                if 0x80 <= number <= 0x9f:
                    return chr(number).decode('cp1252')
            except ValueError:
                number = None
        else:
            if entity_body in keep:
                return m.group(0)
            else:
                number = name2codepoint.get(entity_body)
        if number is not None:
            try:
                return unichr(number)
            except ValueError:
                pass

        return u'' if remove_illegal else m.group(0)

    return _ent_re.sub(convert_entity, to_unicode(text, encoding))
