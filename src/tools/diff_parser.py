import re
from typing import Dict, List, Optional


def parse_diff(git_diff: str) -> Dict[str, List[dict]]:
    """
    Parses a unified git diff into a map of:
        { file_path: [ {line_number, content, type}, ... ] }
    Only includes lines that exist in the NEW version of the file
    (i.e. 'added' and 'context' lines — removed lines are excluded
    since they have no valid position to comment on).
    """
    file_map: Dict[str, List[dict]] = {}
    current_file: Optional[str] = None
    new_line_num: Optional[int] = None

    file_header_re = re.compile(r'^\+\+\+ b/(.+)$')
    hunk_header_re = re.compile(r'^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@')

    for raw_line in git_diff.splitlines():
        file_match = file_header_re.match(raw_line)
        if file_match:
            current_file = file_match.group(1).strip()
            if current_file not in file_map:
                file_map[current_file] = []
            continue

        hunk_match = hunk_header_re.match(raw_line)
        if hunk_match:
            new_line_num = int(hunk_match.group(1))
            continue

        if current_file is None or new_line_num is None:
            continue

        if raw_line.startswith('+') and not raw_line.startswith('+++'):
            file_map[current_file].append({
                "line_number": new_line_num,
                "content": raw_line[1:],
                "type": "added"
            })
            new_line_num += 1
        elif raw_line.startswith('-') and not raw_line.startswith('---'):
            # removed line — does not exist in new file, no line_number to assign
            continue
        elif raw_line.startswith('\\'):
            # "\ No newline at end of file" marker — ignore
            continue
        else:
            # context line (unchanged, present in both old and new)
            file_map[current_file].append({
                "line_number": new_line_num,
                "content": raw_line[1:] if raw_line.startswith(' ') else raw_line,
                "type": "context"
            })
            new_line_num += 1

    return file_map


def validate_line_number(
    file_map: Dict[str, List[dict]],
    file_name: str,
    claimed_line_number: Optional[int],
    line_snippet: str
) -> Optional[int]:
    """
    Checks whether the LLM's claimed line_number actually corresponds to an
    'added' line in the diff for that file. If not, attempts to recover the
    correct line by matching line_snippet content. Returns a validated
    line_number, or None if it can't be confidently resolved.
    """
    if file_name not in file_map:
        print(f"[DIFF VALIDATION] File '{file_name}' not found in diff — cannot validate.")
        return None

    entries = file_map[file_name]
    added_entries = [e for e in entries if e["type"] == "added"]

    # 1. Trust but verify: does the claimed line_number exist as an added line?
    if claimed_line_number is not None:
        for entry in added_entries:
            if entry["line_number"] == claimed_line_number:
                return claimed_line_number
        print(f"[DIFF VALIDATION] Claimed line {claimed_line_number} not an added line in '{file_name}' — attempting snippet match.")

    # 2. Fallback: match on line_snippet content
    if not line_snippet:
        return None

    # Use the first non-empty line of the snippet as the anchor for matching
    snippet_lines = [l.strip() for l in line_snippet.splitlines() if l.strip()]
    if not snippet_lines:
        return None
    anchor = snippet_lines[0]

    matches = [
        e for e in added_entries
        if anchor in e["content"] or e["content"].strip() in anchor
    ]

    if len(matches) == 1:
        print(f"[DIFF VALIDATION] Recovered line {matches[0]['line_number']} via snippet match.")
        return matches[0]["line_number"]
    elif len(matches) > 1:
        print(f"[DIFF VALIDATION] Snippet matched {len(matches)} lines in '{file_name}' — ambiguous, discarding.")
        return None
    else:
        print(f"[DIFF VALIDATION] No snippet match found in '{file_name}' — discarding line_number.")
        return None