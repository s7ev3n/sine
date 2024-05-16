import requests

from sine.actions.base_action import BaseAction, tool_api
from sine.common.logger import logger
from sine.common.utils import is_valid_url


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

        try:
            response = requests.get(jina_url, timeout=5)
        except Exception as e:
            return -1, str(e)

        return response.status_code, response.text
