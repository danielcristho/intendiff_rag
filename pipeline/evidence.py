"""Run checks with: python -m unittest discover -s tests -p test_evidence.py."""
import re

HUNK = re.compile(r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@')


def index_diff(diff):
    records = []
    path = None
    old = new = left_old = left_new = 0
    for number, text in enumerate(diff.splitlines(), 1):
        match = HUNK.match(text)
        kind, old_line, new_line = 'metadata', None, None
        if match:
            old, old_count, new, new_count = match.groups()
            old, new = int(old), int(new)
            left_old = int(old_count) if old_count is not None else 1
            left_new = int(new_count) if new_count is not None else 1
            kind = 'hunk'
        elif (left_old or left_new) and text.startswith(('+', '-', ' ')):
            if text[0] == '+':
                kind, new_line = 'added', new
                new, left_new = new + 1, left_new - 1
            elif text[0] == '-':
                kind, old_line = 'deleted', old
                old, left_old = old + 1, left_old - 1
            else:
                kind, old_line, new_line = 'context', old, new
                old, new = old + 1, new + 1
                left_old, left_new = left_old - 1, left_new - 1
            if left_old < 0 or left_new < 0:
                raise ValueError('Diff hunk exceeds its declared line counts')
        elif text.startswith('diff '):
            path = None
            left_old = left_new = 0
        elif text.startswith('+++ '):
            path = text[4:].split('\t', 1)[0]
            if path.startswith('b/'):
                path = path[2:]
        records.append({'id': f'D{number:05d}', 'kind': kind, 'path': path,
                        'old_line': old_line, 'new_line': new_line, 'text': text})
    # A truncated final hunk remains indexable; missing lines are never invented.
    return records


def render_diff(diff):
    return '\n'.join(f"[{r['id']} {r['kind']}] {r['text']}" for r in index_diff(diff))


def audit_ids(diff, ids):
    index = {r['id']: r for r in index_diff(diff)}
    found = [index[x] for x in ids if x in index]
    return {'unknown_ids': [x for x in ids if x not in index],
            'duplicate_ids': len(ids) - len(set(ids)),
            'referenced_lines': found,
            'changed_line_count': sum(r['kind'] in ['added', 'deleted'] for r in found),
            'content_line_count': sum(r['kind'] in ['added', 'deleted', 'context'] for r in found),
            'semantic_support_verified': False}
