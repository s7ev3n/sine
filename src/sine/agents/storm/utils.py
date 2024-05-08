import json
import re

import requests
from bs4 import BeautifulSoup


def load_json(file_path):
    with open(file_path) as f:
        data = json.load(f)

    return data

def save_json(file_path, data):
    with open(file_path, 'w') as f:
        json.dump(data, f)

    return True

def save_txt(file_path, data):
    with open(file_path, 'w') as f:
        f.write(data)

    return True

def load_txt(file_path):
    with open(file_path) as f:
        data = f.read()

    return data

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


def limit_word_count_preserve_newline(input_string, max_word_count):
        """
        Limit the word count of an input string to a specified maximum, while preserving the integrity of complete lines.

        The function truncates the input string at the nearest word that does not exceed the maximum word count,
        ensuring that no partial lines are included in the output. Words are defined as text separated by spaces,
        and lines are defined as text separated by newline characters.

        Args:
            input_string (str): The string to be truncated. This string may contain multiple lines.
            max_word_count (int): The maximum number of words allowed in the truncated string.

        Returns:
            str: The truncated string with word count limited to `max_word_count`, preserving complete lines.
        """

        word_count = 0
        limited_string = ''

        for word in input_string.split('\n'):
            line_words = word.split()
            for lw in line_words:
                if word_count < max_word_count:
                    limited_string += lw + ' '
                    word_count += 1
                else:
                    break
            if word_count >= max_word_count:
                break
            limited_string = limited_string.strip() + '\n'

        return limited_string.strip()
