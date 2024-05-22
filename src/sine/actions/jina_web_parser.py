import re

import requests

from sine.actions.base_action import BaseAction, tool_api
from sine.common.logger import logger
from sine.common.utils import is_valid_url


def is_blocked(text):
    # pre-defined keywords pattern if the scraper is blocked
    blocked_keywords = ['you are blocked', 'access denied', 'unauthorized']

    pattern = '|'.join(re.escape(keyword) for keyword in blocked_keywords)
    match = re.search(pattern, text, re.IGNORECASE)

    if match:
        return True

    return False

class JinaWebParser(BaseAction):
    '''JinaWebParser parse given web url content into markdown format.'''
    jina_reader_prefix = 'https://r.jina.ai/'

    @tool_api
    def run(self, url: str):
        '''
        Args:
            url (str): the url to parse

        Returns:
            content (str): web url content in markdown format
        '''
        if is_valid_url(url):
            jina_url = self.jina_reader_prefix + url
        else:
            logger.error(f"Invalid URL {url}")
            return -1, ''

        try:
            response = requests.get(jina_url, timeout=5)
        except Exception as e:
            return -1, str(e)

        if is_blocked(response.text):
            return -1, 'Blocked by the website'

        return response.status_code, _process_markdown_content(response.text)

def _process_markdown_content(text):
    parts = text.split("Markdown Content:", 1)
    if len(parts) > 1:
        return parts[1].strip()
    else:
        return text
