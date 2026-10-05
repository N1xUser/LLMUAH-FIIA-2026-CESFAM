import re


def format_for_whatsapp(text: str) -> str:

    def _strip_header(match: re.Match) -> str:
        content = match.group(1).strip()
        if content.startswith("**") and content.endswith("**"):
            content = content[2:-2]
        elif content.startswith("*") and content.endswith("*"):
            content = content[1:-1]
        return f"*{content}*"

    text = re.sub(r"^#{1,6}[ \t]*(.+)$", _strip_header, text, flags=re.MULTILINE)

    text = re.sub(r"\*\*(.+?)\*\*", r"*\1*", text)

    text = re.sub(r"^[ \t]*([-*_]){3,}[ \t]*$", "", text, flags=re.MULTILINE)

    text = re.sub(r"^[ \t]*[-*][ \t]+", "• ", text, flags=re.MULTILINE)

    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def strip_markdown(text: str) -> str:

    text = format_for_whatsapp(text)
    text = text.replace("*", "").replace("•", "-")
    return text