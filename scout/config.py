"""Config loading — stdlib-only YAML reader for our own controlled config files.

PyYAML is NOT in the stdlib and pip is banned in the core path (hard constraint).
Since WE author config/subject.yaml and config/sources.yaml, we only need to parse
a small, well-defined YAML subset:

    - block mappings:      key: value
    - nested mappings via 2-space indentation
    - block sequences:     - item      (scalars or inline maps)
    - inline flow lists:    [a, b, c]
    - inline flow maps:     {id: x, url: y}
    - scalars:              str / int / float / bool / null, quoted or bare
    - comments:             # to end of line   (not inside quotes)

If you need a construct outside this subset, keep the config simple instead of
reaching for pip. This keeps the runtime dependency-free everywhere.
"""

from __future__ import annotations

import os

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(REPO_ROOT, "config")


# --------------------------------------------------------------------------- #
# Scalar coercion
# --------------------------------------------------------------------------- #
def _scalar(raw: str):
    s = raw.strip()
    if s == "" or s in ("~", "null", "Null", "NULL"):
        return None
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ("'", '"'):
        return s[1:-1]
    low = s.lower()
    if low in ("true", "yes", "on"):
        return True
    if low in ("false", "no", "off"):
        return False
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        pass
    return s


def _strip_comment(line: str) -> str:
    out, in_s, in_d = [], False, False
    for ch in line:
        if ch == "'" and not in_d:
            in_s = not in_s
        elif ch == '"' and not in_s:
            in_d = not in_d
        elif ch == "#" and not in_s and not in_d:
            break
        out.append(ch)
    return "".join(out)


def _parse_flow(s: str):
    """Parse an inline [..] list or {..} map. Nested flow supported minimally."""
    s = s.strip()
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        return [_scalar(p) for p in _split_flow(inner)] if inner else []
    if s.startswith("{") and s.endswith("}"):
        inner = s[1:-1].strip()
        out: dict = {}
        if inner:
            for part in _split_flow(inner):
                if ":" in part:
                    k, v = part.split(":", 1)
                    out[k.strip()] = _scalar(v)
        return out
    return _scalar(s)


def _split_flow(s: str) -> list[str]:
    """Split on commas that are not inside quotes or nested brackets."""
    parts, depth, in_s, in_d, cur = [], 0, False, False, []
    for ch in s:
        if ch == "'" and not in_d:
            in_s = not in_s
        elif ch == '"' and not in_s:
            in_d = not in_d
        elif not in_s and not in_d:
            if ch in "[{":
                depth += 1
            elif ch in "]}":
                depth -= 1
            elif ch == "," and depth == 0:
                parts.append("".join(cur))
                cur = []
                continue
        cur.append(ch)
    if "".join(cur).strip():
        parts.append("".join(cur))
    return [p.strip() for p in parts]


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def parse_yaml(text: str):
    """Parse the supported YAML subset into Python dict/list/scalars."""
    lines = []
    for raw in text.splitlines():
        stripped = _strip_comment(raw)
        if stripped.strip() == "":
            continue
        lines.append(stripped)

    pos = 0

    def parse_block(min_indent: int):
        nonlocal pos
        # Decide list vs map by first line at this indent.
        if pos >= len(lines):
            return None
        first = lines[pos]
        ind = _indent(first)
        if ind < min_indent:
            return None
        is_list = first.lstrip().startswith("- ")

        if is_list:
            result: list = []
            while pos < len(lines):
                line = lines[pos]
                cind = _indent(line)
                if cind < ind or not line.lstrip().startswith("- "):
                    break
                content = line.lstrip()[2:].strip()
                pos += 1
                if content == "":
                    result.append(parse_block(ind + 1))
                elif content.startswith(("[", "{")):
                    result.append(_parse_flow(content))
                elif ":" in content and content[0] not in "'\"":
                    # inline map entry starting the item, possibly with more keys nested
                    k, v = content.split(":", 1)
                    item = {k.strip(): _value_or_block(v, ind + 1)}
                    while pos < len(lines) and _indent(lines[pos]) > ind and not lines[pos].lstrip().startswith("- "):
                        k2, v2 = lines[pos].lstrip().split(":", 1)
                        pos += 1
                        item[k2.strip()] = _value_or_block(v2, ind + 2)
                    result.append(item)
                else:
                    result.append(_scalar(content))
            return result

        # map
        result_map: dict = {}
        while pos < len(lines):
            line = lines[pos]
            cind = _indent(line)
            if cind != ind or line.lstrip().startswith("- "):
                if cind < ind:
                    break
                if cind > ind:
                    break
                break
            key_part = line.lstrip()
            if ":" not in key_part:
                break
            key, val = key_part.split(":", 1)
            pos += 1
            result_map[key.strip()] = _value_or_block(val, ind + 1)
        return result_map

    def _value_or_block(val: str, child_indent: int):
        v = val.strip()
        if v == "":
            # nested block if the following line is more indented
            if pos < len(lines) and _indent(lines[pos]) >= child_indent:
                return parse_block(child_indent)
            if pos < len(lines) and lines[pos].lstrip().startswith("- ") and _indent(lines[pos]) >= child_indent - 1:
                return parse_block(_indent(lines[pos]))
            return None
        if v.startswith(("[", "{")):
            return _parse_flow(v)
        return _scalar(v)

    parsed = parse_block(0)
    return parsed if parsed is not None else {}


def load_yaml_file(path: str):
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as fh:
        return parse_yaml(fh.read())


def load_sources() -> dict:
    return load_yaml_file(os.path.join(CONFIG_DIR, "sources.yaml")) or {}


def load_subject() -> dict:
    return load_yaml_file(os.path.join(CONFIG_DIR, "subject.yaml")) or {}
