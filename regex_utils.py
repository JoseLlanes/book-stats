"""Regular expressions used by the analysis modules."""

import re

# Construct the accented character by code point to avoid source-encoding ambiguity.
chapter_pattern = re.compile(
    rf"^\s*(?:CAP[I{chr(0x00CD)}]TULO|CHAPTER)\s+([IVXLCDM]+|\d+)\b[^\r\n]*$",
    re.IGNORECASE | re.MULTILINE,
)
