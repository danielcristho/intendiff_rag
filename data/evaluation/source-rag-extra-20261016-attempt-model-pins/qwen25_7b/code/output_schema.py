"""Shared D101 output constraints for every model and experimental configuration."""
SCHEMA = {
    'type': 'object',
    'properties': {
        'evidence': {'type': 'array', 'maxItems': 1,
                     'items': {'type': 'string', 'maxLength': 200}},
        'reason': {'type': 'string', 'maxLength': 240},
        'verdict': {'type': 'string', 'enum': ['malicious', 'benign']},
    },
    'required': ['evidence', 'reason', 'verdict'],
    'additionalProperties': False,
}

RESPONSE_FORMAT = {'type': 'json_schema', 'json_schema': {
    'name': 'update_decision', 'strict': True, 'schema': SCHEMA,
}}
