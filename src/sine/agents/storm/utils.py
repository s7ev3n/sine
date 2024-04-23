import re

import requests
from bs4 import BeautifulSoup


def get_wiki_page_title_and_toc(url):
    """Get the main title and table of contents from an url of a Wikipedia page."""

    response = requests.get(url, timeout=5)
    soup = BeautifulSoup(response.content, "html.parser")

    # Get the main title from the first h1 tag
    main_title = soup.find("h1").text.replace("[edit]", "").strip().replace("\xa0", " ")

    toc = ""
    levels = []
    excluded_sections = {
        "Contents",
        "See also",
        "Notes",
        "References",
        "External links",
    }

    # Start processing from h2 to exclude the main title from TOC
    for header in soup.find_all(["h2", "h3", "h4", "h5", "h6"]):
        level = int(
            header.name[1]
        )  # Extract the numeric part of the header tag (e.g., '2' from 'h2')
        section_title = header.text.replace("[edit]", "").strip().replace("\xa0", " ")
        if section_title in excluded_sections:
            continue

        while levels and level <= levels[-1]:
            levels.pop()
        levels.append(level)

        indentation = "  " * (len(levels) - 1)
        toc += f"{indentation}{section_title}\n"

    return main_title, toc.strip()


def clean_up_outline(outline, topic=""):
    output_lines = []
    current_level = 0  # To track the current section level

    for line in outline.split("\n"):
        stripped_line = line.strip()

        if topic != "" and f"# {topic.lower()}" in stripped_line.lower():
            output_lines = []

        # Check if the line is a section header
        if stripped_line.startswith("#"):
            current_level = stripped_line.count("#")
            output_lines.append(stripped_line)
        # Check if the line is a bullet point
        elif stripped_line.startswith("-"):
            subsection_header = (
                "#" * (current_level + 1) + " " + stripped_line[1:].strip()
            )
            output_lines.append(subsection_header)

    outline = "\n".join(output_lines)

    # Remove references.
    outline = re.sub(r"#[#]? See also.*?(?=##|$)", "", outline, flags=re.DOTALL)
    outline = re.sub(r"#[#]? See Also.*?(?=##|$)", "", outline, flags=re.DOTALL)
    outline = re.sub(r"#[#]? Notes.*?(?=##|$)", "", outline, flags=re.DOTALL)
    outline = re.sub(r"#[#]? References.*?(?=##|$)", "", outline, flags=re.DOTALL)
    outline = re.sub(r"#[#]? External links.*?(?=##|$)", "", outline, flags=re.DOTALL)
    outline = re.sub(r"#[#]? External Links.*?(?=##|$)", "", outline, flags=re.DOTALL)
    outline = re.sub(r"#[#]? Bibliography.*?(?=##|$)", "", outline, flags=re.DOTALL)
    outline = re.sub(r"#[#]? Further reading*?(?=##|$)", "", outline, flags=re.DOTALL)
    outline = re.sub(r"#[#]? Further Reading*?(?=##|$)", "", outline, flags=re.DOTALL)
    outline = re.sub(r"#[#]? Summary.*?(?=##|$)", "", outline, flags=re.DOTALL)
    outline = re.sub(r"#[#]? Appendices.*?(?=##|$)", "", outline, flags=re.DOTALL)
    outline = re.sub(r"#[#]? Appendix.*?(?=##|$)", "", outline, flags=re.DOTALL)

    return outline


def process_table_of_contents(toc):
    """Convert a table of contents into a tree structure.

    The table of contents is a string with each line representing a heading.
    "#" Title"  indicates section title, "##" Title" to indication subsection title, "###" Title" to indicate subsubsection title, and so on.
    """
    lines = toc.split("\n")

    root = {}
    path = [(root, -1)]

    for line in lines:
        line = line.strip()
        if not line.startswith("#"):
            continue

        # Count only the leading '#' symbols
        level = 0
        for char in line:
            if char == "#":
                level += 1
            else:
                break

        heading = line[level:].strip()
        if len(heading) == 0:
            continue
        while path and path[-1][1] >= level:
            path.pop()

        # Add the new heading
        if path:
            current_dict = path[-1][0]
            current_dict[heading] = {}
            path.append((current_dict[heading], level))

    return root
