from abc import ABC
from typing import Dict, List, Optional

from sine.common.logger import logger


class SectionNode:
    """SectionNode is abstraction of (sub)sections of an article. Article is consist of SectionNodes."""

    def __init__(self, section_name: str, level: int, content=None) -> None:
        self.section_name = section_name
        self.level = level # topic is level 0, # is level 1, etc
        self.content = content
        self.children = []
        self.preference = None # section writing preferences

    def add_child(self, new_child_node, insert_to_front=False):
        if insert_to_front:
            self.children.insert(0, new_child_node)
        else:
            self.children.append(new_child_node)

    def remove_child(self, child):
        self.children.remove(child)

class Article(ABC):
    """Article is consist of ArticleNodes in a Tree Data Structure.

    NOTE: Article is abstraction and operation for the outline of the article,
    and writer generates content for each SectionNode.
    """

    def __init__(self, topic_name):
        self.root = SectionNode(section_name=topic_name, level=0)

    def get_outline_tree(self):

        def build_tree(node) -> Dict[str, Dict]:
            tree = {}
            for child in node.children:
                tree[child.section_name] = build_tree(child)

            return tree if tree else {}

        return build_tree(self.root)

    def get_first_level_section_names(self) -> List[str]:
        """Get first level section names of the article, i.e. the first level of artilce outline."""

        return [i.section_name for i in self.root.children]

    def get_subsection_names_as_list(self, section_name: str, with_hashtags: bool = False) -> List[str]:
        """Get the list of subsection names under a section."""

        section_node = self.find_section(self.root, section_name)
        if not section_node:
            logger.error(f"Section {section_name} not found.")
            return []

        subsection_names = []

        def preorder_traverse(node):
            prefix = "#" * node.level if with_hashtags else ""  # Adjust level if excluding root
            subsection_names.append(f"{prefix} {node.section_name}".strip() if with_hashtags else node.section_name)
            for child in node.children:
                preorder_traverse(child)

        preorder_traverse(section_node)

        return subsection_names

    def find_section(self, root_node: SectionNode, section_name: str) -> Optional[SectionNode]:
        """
        Return the node of the section given the section name.

        Args:
            root: the root node of search
            section_name: the name of node as section name

        Return:
            reference of the node or None if section name has no match
        """
        if root_node.section_name == section_name:
            return root_node

        for child in root_node.children:
            result = self.find_section(child, section_name)
            if result:
                return result

        return None

    @classmethod
    def from_dict(cls, topic: str, article_dict: Dict):
        """Construct article from article dict.

        Args:
            article_dict: article dict a nested dict where key is section name and value is content

        Returns:
            Article object
        """

    def to_dict(self):
        pass

    def string(self):
        """export article to string in markdown format."""

    @classmethod
    def from_outline_string(cls, topic: str, outline: str):
        """Construct article with outline from outline string.

        Args:
            outline: outline string in markdown format where section has hashtag (#)

        Returns:
            Article instance with outline
        """
        lines = []
        try:
            lines = outline.split('\n')
            lines = [line.strip() for line in lines if line.strip()]
        except:
            if not len(lines):
                logger.critical("Error in parsing outline string, no outline structure found.")
            exit()

        article = cls(topic, 0) # topic as the root node

        # deal with the case where topic is the first line of the outline and with # hashtag
        is_topic_first_line = lines[0].startswith('#') and \
            lines[0].replace('#', '').strip().lower() == topic.strip().lower().replace('_', ' ')
        if is_topic_first_line:
            lines = lines[1:]

        node_stack = [article.root] # stack to help find where curent node should be inserted
        for line in lines:
            level = line.count('#') - is_topic_first_line
            section_name = line.replace('#', '').strip()
            new_node = SectionNode(section_name, level)

            # pop out all the nodes in the stack that are at lower level
            while node_stack and level <= node_stack[-1].level:
                node_stack.pop()

            # insert the new node to the parent node
            parent_node = node_stack[-1]
            parent_node.add_child(new_node)

            node_stack.append(new_node)

        return article
