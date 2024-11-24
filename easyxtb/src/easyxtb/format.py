"""Pretty print CJSON files but with flattened arrays for improved readability without
significantly increasing footprint."""

import json


def _flatten_arrays(data: dict) -> dict:
    """Turn any lists of simple items (not dicts or lists) into strings."""
    if isinstance(data, list):
        # Turn simple lists into flat strings
        if all(not isinstance(i, (dict, list)) for i in data):
            return json.dumps(data)
        # Recursively flatten any nested lists
        else:
            items = [_flatten_arrays(i) for i in data]
            return items
    elif isinstance(data, dict):
        # Recursively flatten all entries
        new = {k: _flatten_arrays(v) for k, v in data.items()}
        return new
    else:
        return data


def cjson_dumps(
    cjson: dict,
    prettyprint=True,
    indent=2,
    **kwargs,
) -> str:
    """Serialize a CJSON object to a JSON formatted string.
    
    With the default `prettyprint` option, all simple arrays (not themselves containing
    objects/dicts or arrays/lists) will be flattened onto a single line, while all other
    array elements and object members will be pretty-printed with the specified indent
    level (2 spaces by default).

    `indent` and any `**kwargs` are passed to Python's `json.dumps()` as is, so the same
    values are valid e.g. `indent=0` will insert newlines while `indent=None` will
    afford a compact single-line representation.
    """
    if prettyprint:
        flattened = _flatten_arrays(cjson)
        # Lists are now strings, remove quotes to turn them back into lists
        cjson_string = (
            json.dumps(flattened, indent=indent, **kwargs)
            .replace('"[', '[').replace(']"', ']')
        )
        # Any strings within lists will have had their quotes escaped, so get rid of escapes
        cjson_string = cjson_string.replace(r'\"', '"')
    else:
        cjson_string = json.dumps(cjson, indent=indent, **kwargs)
    return cjson_string
