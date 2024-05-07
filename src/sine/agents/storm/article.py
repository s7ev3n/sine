from abc import ABC
from typing import Dict, List, Optional

from sine.common.logger import logger


class SectionNode:
    """SectionNode is abstraction of (sub)sections of an article. Article is consist of SectionNodes."""

    def __init__(self, section_name: str, level: int, content: str = None) -> None:
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

    Article level:
        topic         : level 0
        section       : level 1
        subsection    : level 2
        subsubsection : level 3
        etc...

    NOTE: Article is abstraction and operation for the outline of the article,
    and writer generates content for each SectionNode.
    """

    def __init__(self, topic_name):
        self.root = SectionNode(section_name=topic_name, level=0)

    def get_first_level_outline(self) -> List[str]:
        """Get first level artilce outline, i.e. the first level of section names of the article."""

        return [i.section_name for i in self.root.children]

    def get_sublevel_outline_as_list(self, section_name: str, with_hashtags: bool = False) -> List[str]:
        """Get the list of subsection names under a section, including the section_name itself."""

        section_node = self.find_section(self.root, section_name)
        if not section_node:
            logger.error(f"Section {section_name} not found.")
            return []

        subsection_names = []

        def preorder_traverse(node):
            prefix = "#" * node.level if with_hashtags else ""
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

    def update_section_content(self, section_name: str, content: str):
        """Update the content of the section with the given section name."""

        section_node = self.find_section(self.root, section_name)
        if not section_node:
            logger.error(f"Section {section_name} not found.")
            return

        section_node.content = content

    def add_new_subsection(self, parent_section_name: str, new_section_name: str, content: str = None):
        """Add new sublevel section to sepcific section."""

        parent_section_node = self.find_section(self.root, parent_section_name)
        if not parent_section_node:
            logger.error(f"Parent section {parent_section_name} not found.")
            return

        new_section_node = SectionNode(new_section_name, parent_section_node.level + 1, content)
        parent_section_node.add_child(new_section_node)

    def to_dict(self):
        """Export Article instance to article dict.

        article_dict format:
        {
            'section_name': {
                'content': 'content of the section',
                'subsections': {
                    'subsection_name': {
                        'content': 'content of the subsection',
                        'subsections': {
                            // etc ...
                        }
                    }
                }
            }
        }
        """

        def transverse_tree(node) -> Dict[str, Dict]:
            tree = {
                node.section_name: {
                    'content' : node.content,
                    'subsections': {}
                }
            }

            for child in node.children:
                tree[node.section_name]['subsections'].update(transverse_tree(child))

            return tree if tree else {}

        return transverse_tree(self.root)

    def to_string(self):
        """Export the whole article to string in markdown format."""

        article_str = ''

        def traverse_tree(node):
            nonlocal article_str
            article_str += f"{'#' * node.level} {node.section_name}\n"
            if node.content:
                article_str += f"{node.content}\n"

            for child in node.children:
                traverse_tree(child)

        traverse_tree(self.root)

        return article_str

    @classmethod
    def create_from_outline_string(cls, topic: str, outline: str):
        """Construct Article instance's outline from outline string.

        Args:
            outline: outline string in markdown format where section has hashtag (#)

        Returns:
            Article instance with outline, i.e. the tree structure of the article
        """
        lines = []
        try:
            lines = outline.split('\n')
            lines = [line.strip() for line in lines if line.strip()]
        except:
            if not len(lines):
                logger.critical("Error in parsing outline string, no outline structure found.")
            exit()

        article = cls(topic) # topic as the root node

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
