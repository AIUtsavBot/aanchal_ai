def json_to_toon(data, indent=0):
    def fmt_value(v, level):
        if isinstance(v, dict):
            return json_to_toon(v, level)
        if isinstance(v, list):
            if not v:
                return ""
            lines = []
            for item in v:
                iv = fmt_value(item, indent + 2)
                if iv:
                    lines.append(" " * (indent + 2) + f"- {iv.strip()}")
            return "\n" + "\n".join(lines)
        if v is None:
            return ""
        return str(v)

    import re
    lines = []
    for k, v in (data or {}).items():
        key = re.sub(r"[\"'{}]+", "", str(k)).strip()
        val = fmt_value(v, indent)
        if isinstance(v, (dict, list)) and val.startswith("\n"):
            lines.append(" " * indent + f"{key}:")
            lines.append(val.strip("\n"))
        else:
            if val:
                lines.append(" " * indent + f"{key}: {val}")
    return "\n".join(lines)
