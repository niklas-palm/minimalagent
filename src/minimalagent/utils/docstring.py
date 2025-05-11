"""Docstring parsing utilities for MinimalAgent."""

# Standard library imports
import inspect
import re
from typing import Any, Dict, List, Optional, Tuple


class DocstringParser:
    """Parser for Google-style docstrings."""

    # Regular expression patterns
    SECTION_PATTERN = (
        r"^\s*[A-Za-z_]+:"  # Matches section headers like "Args:", "Returns:"
    )
    PARAM_PATTERN = r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:\([^)]*\))?\s*:\s*(.*)$"  # Matches "param: description"

    @classmethod
    def parse(cls, func: Any) -> Tuple[str, str, Dict[str, str]]:
        """
        Parse docstring from a function object.

        Args:
            func: Function to extract docstring from

        Returns:
            Tuple of (short_description, long_description, param_descriptions)
        """
        if not func.__doc__:
            return "", "", {}

        # Clean up the docstring
        docstring = inspect.cleandoc(func.__doc__)

        # Extract the short description (first line)
        lines = docstring.split("\n")
        short_description = lines[0].strip()

        # Find the Args section
        args_section = cls._find_section(lines, "args")

        # If no Args section was found, return with no parameters
        if not args_section:
            long_description = cls._extract_long_description(lines)
            return short_description, long_description, {}

        args_start, args_end = args_section

        # Extract parameter descriptions
        param_descriptions = cls._extract_parameters(lines, args_start, args_end)

        # Get long description (anything between first line and Args section)
        long_description = cls._extract_long_description(lines, end=args_start)

        return short_description, long_description, param_descriptions

    @classmethod
    def _find_section(
        cls, lines: List[str], section_name: str
    ) -> Optional[Tuple[int, int]]:
        """
        Find a section in the docstring by name.

        Args:
            lines: Docstring lines
            section_name: Name of section to find (e.g., 'args', 'returns')

        Returns:
            Tuple of (start_line, end_line) if found, None otherwise
        """
        section_start = None
        section_end = None

        # Convert to lowercase for case-insensitive matching
        section_name = section_name.lower()

        for i, line in enumerate(lines):
            line_lower = line.strip().lower()

            # Look for the section start (e.g., 'Args:')
            if (
                line_lower == f"{section_name}:"
                or line_lower.startswith(f"{section_name}:")
            ) and section_start is None:
                section_start = i

                # Find where the section ends
                for j in range(i + 1, len(lines)):
                    # Section ends when another section begins
                    if re.match(cls.SECTION_PATTERN, lines[j]) and not re.match(
                        r"^\s+[a-zA-Z_][a-zA-Z0-9_]*:", lines[j]
                    ):
                        section_end = j
                        break
                break

        # If we found a start but no end, the section goes to the end of the docstring
        if section_start is not None and section_end is None:
            section_end = len(lines)

        return (section_start, section_end) if section_start is not None else None

    @classmethod
    def _extract_parameters(
        cls, lines: List[str], start: int, end: int
    ) -> Dict[str, str]:
        """
        Extract parameter descriptions from the Args section.

        Args:
            lines: Docstring lines
            start: Start line of the Args section
            end: End line of the Args section

        Returns:
            Dictionary mapping parameter names to descriptions
        """
        param_descriptions = {}
        current_param = None
        current_desc = []

        for i in range(start + 1, end):
            line = lines[i].strip()
            if not line:
                continue

            # Match parameter definition: "param: description" or "param (optional): description"
            param_match = re.match(cls.PARAM_PATTERN, line)
            if param_match:
                # Save previous parameter if any
                if current_param and current_desc:
                    param_descriptions[current_param] = " ".join(current_desc).strip()

                current_param = param_match.group(1)
                current_desc = [param_match.group(2).strip()]
            elif current_param:
                # Continue parameter description
                current_desc.append(line)

        # Save the last parameter
        if current_param and current_desc:
            param_descriptions[current_param] = " ".join(current_desc).strip()

        return param_descriptions

    @classmethod
    def _extract_long_description(
        cls, lines: List[str], start: int = 1, end: Optional[int] = None
    ) -> str:
        """
        Extract the long description from docstring lines.

        Args:
            lines: Docstring lines
            start: Start line for extraction (default: 1, after short description)
            end: Optional end line for extraction

        Returns:
            Formatted long description string
        """
        if end is None:
            # If no end is specified, stop at the first section marker
            long_desc_lines = []
            for i, line in enumerate(lines[start:], start):
                if re.match(cls.SECTION_PATTERN, line):
                    break
                if line.strip():
                    long_desc_lines.append(line.strip())
        else:
            # Extract up to the specified end line
            long_desc_lines = [
                line.strip() for line in lines[start:end] if line.strip()
            ]

        return " ".join(long_desc_lines)
