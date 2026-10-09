import re


chapter_pattern = re.compile(
    r"^\s*(?:CAP[IÍ]TULO|CHAPTER)\s+"
    r"([IVXLCDM]+|\d+)\b",
    re.IGNORECASE | re.MULTILINE,
)
