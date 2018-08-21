"""Make JSON acceptable by GraphQL.

Replace special characters in JSON keys to be accepted by GraphQL.
The dictionary `key_map` allows mapping between old and new keys.
"""
import re
import unidecode


class JSonCleaning:

    key_map = {}
    reversed_key_map = {}

    @classmethod
    def strip_special_char(cls, txt):
        """Convert a string by removing diacritics and replacing special characters with underscores.

        Arguments:
            txt {string} -- text to be transformed

        Returns:
            string -- new text that complies with GraphQL key convention: `Names must match /^[_a-zA-Z][_a-zA-Z0-9]*$/`
        """
        if txt in cls.key_map:
            return cls.key_map[txt]
        unaccented = unidecode.unidecode(txt)
        unaccented = re.sub(r'\W','_',unaccented)
        if unaccented[0] in range(10):
            unaccented = '_' + unaccented
        new_txt = unaccented
        suffix = 0
        while new_txt in cls.key_map.values():
            new_txt = unaccented + str(suffix)
            suffix += 1
        cls.key_map[txt] = new_txt
        return new_txt

    @classmethod
    def restore_special_char(cls, txt):
        return cls.reversed_key_map[txt]


    @classmethod
    def _encode_decode_json_str(cls, json, func):
        pattern = re.compile(r'(?:(?:")([^\"]+)(?:":))|(?:(?:\')([^\']+)(?:\':))')
        match_iter = pattern.finditer(json)
        new_json = []
        last_end = 0
        for match in match_iter:
            n = 1 if match.group(1) else 2
            repl = func(match.group(n))
            beg, end = match.span(n)
            new_json.append(json[last_end:beg])
            new_json.append(repl)
            last_end = end
        new_json.append(json[last_end:])
        new_json = ''.join(new_json)
        return new_json

    @classmethod
    def _encode_decode_json_dict(cls, d, convert_function):
        """
        Convert a nested dictionary from one convention to another.

        Arguments:
            d {dict} -- dictionary (nested or not) to be converted.
            convert_function {func} -- function that takes the string in one convention and returns it in the other one.
        Returns:
            dict -- dictionary with the new keys.
        """
        new = {}
        for k, v in d.items():
            new_v = v
            if isinstance(v, dict):
                new_v = cls._encode_decode_json_dict(v, convert_function)
            elif isinstance(v, list):
                new_v = list()
                for x in v:
                    if isinstance(x, dict):
                        new_v.append(cls._encode_decode_json_dict(x, convert_function))
                    else:
                        new_v.append(x)
            new[convert_function(k)] = new_v
        return new

    @classmethod
    def clean_keys(cls, json):
        """Transform special characters from keys."""
        if isinstance(json, dict):
            return cls._encode_decode_json_dict(json, cls.strip_special_char)
        return cls._encode_decode_json_str(json, cls.strip_special_char)

    @classmethod
    def restore_keys(cls, json):
        """Convert keys from stripped to original ones."""
        cls.reversed_key_map = dict(map(reversed, cls.key_map.items()))
        if isinstance(json, dict):
            return cls._encode_decode_json_dict(json, cls.restore_special_char)
        return cls._encode_decode_json_str(json, cls.restore_special_char)
