from typing import Dict, List, Optional

from sine.common.logger import logger


class ArticleNode:
    """ArticleNode is abstraction of sections of an article in a Tree Data Structure, equipped with operations."""

    def __init__(self, section_name: str, level: int, content: str = None) -> None:
        self.section_name = section_name
        self.level = level
        self.content = content
        self.children = []
        self.preference = None # section writing preferences

    def add_child(self, new_child_node, insert_to_front=False):
        if insert_to_front:
            self.children.insert(0, new_child_node)
        else:
            self.children.append(new_child_node)

        return True

    def remove_child(self, child):
        self.children.remove(child)

        return True
    
    def update_content(self, content_str):
        self.content = content_str
        
        return True

    def remove_content(self):
        if self.content:
            self.content = None
        
        return True

    def to_dict(self) -> Dict[str, Dict]:
        """
        section dict format:
        {
            'section_name': {
                'content': 'content of the section',
                'level': 1, 
                'children': [
                    'subsection_name_1': {
                        'content': 'content of the subsection',
                        'level': 2,
                        'children': {
                            // etc ...
                        },
                    'subsection_name_2': {
                        'content': 'content of the subsection',
                        'level': 2,
                        'children': {
                            // etc ...
                        },
                    }
                    // etc ...
                    ]
                }
            }
        }
        """

        def dfs(node) -> Dict[str, Dict]:
            tree = {
                node.section_name: {
                    'content' : node.content,
                    'level' : node.level,
                    'children': {},
                    'preference': node.preference
                }
            }

            for child in node.children:
                tree[node.section_name]['children'].update(dfs(child))

            return tree if tree else {}

        return dfs(self)

    def to_string(self):
        """Export the whole article to string in markdown format."""

        node_str = ''

        def traverse_tree(node):
            nonlocal node_str
            if node.level:
                node_str += f"{'#' * node.level} {node.section_name}\n"
            if node.content:
                node_str += f"{node.content}\n"

            for child in node.children:
                traverse_tree(child)

        traverse_tree(self)

        return node_str
    
    def find_node(self, name: str):
        """
        Return the node of the section given the section name.

        Args:
            root: the root node of search
            section_name: the name of node as section name

        Return:
            reference of the node or None if section name has no match
        """
        if self.section_name == name:
            return self

        for child in self.children:
            result = self.find_node(child, child.section_name)
            if result:
                return result

        return None

    def get_children_names(self, include_self: bool = True, with_hashtags: bool = False) -> List[str]:
        """Get the list of children names, including the section_name itself."""
        children_names = []

        def preorder_traverse(node):
            prefix = "#" * node.level if with_hashtags else ""
            children_names.append(f"{prefix} {node.section_name}".strip() if with_hashtags else node.section_name)
            for child in node.children:
                preorder_traverse(child)

        for child in self.children:
            preorder_traverse(child)

        if include_self:
            children_names.insert(0, self.section_name)

        return children_names

    @classmethod
    def create_from_markdown(cls, markdown: str):
        """Create a SectionNode from markdown string."""
        
        lines = []
        try:
            lines = markdown.split('\n')
            lines = [line.strip() for line in lines if line.strip()]
        except:
            logger.error("Error in parsing outline string.")
            return None

        node_stack = [] # stack to help find where curent node should be inserted
        i = 0
        while i < len(lines):
            line = lines[i]
            if line.startswith('#'):
                level = line.count('#')
                section_name = line.replace('#', '').strip()
                new_node = ArticleNode(section_name, level)

                # pop out all the nodes in the stack that are at lower level
                while node_stack and level <= node_stack[-1].level:
                    node_stack.pop()

                # insert the new node to the parent node
                if len(node_stack):
                    parent_node = node_stack[-1]
                    parent_node.add_child(new_node)
                node_stack.append(new_node)

                # Collect all lines as content until the next section starts
                content_lines = []
                i += 1
                while i < len(lines) and not lines[i].startswith('#'):
                    content_lines.append(lines[i])
                    i += 1
                new_node.content = '\n'.join(content_lines).strip()
                continue  # Skip the increment of i to check the current line in the next iteration
            i += 1

        assert len(node_stack) != 0, "No SectionNode created !"

        return node_stack[0]

class Article:
    """Article is consist of ArticleNodes in a Tree Data Structure.

    Article level:
        topic         : level 0 (no hashtag)
        title         : level 1 (#)
        section       : level 2 (##)
        subsection    : level 3 (###)
        subsubsection : level 4 (####)
        etc...

    NOTE: Article is abstraction and operation for the outline of the article,
    and writer generates content for each ArticleNode.
    """

    def __init__(self, topic_name):
        self.root = ArticleNode(section_name=topic_name, level=0)

    @property
    def topic(self):
        return self.root.section_name

    def get_title_node(self):
        assert len(self.root.children) > 0, "No article title found."
        assert len(self.root.children) < 2, f"Found {len(self.root.children)} titles."

        return self.root.children[0]

    def get_sections(self) -> List[str]:
        """Get the section (level 2) names of the article."""
        title_node = self.get_title_node()

        return [i for i in title_node.children]

    def find_section(self, section_name: str) -> Optional[ArticleNode]:
        """
        Return the node of the section given the section name.

        Args:
            section_name: the section name of node

        Return:
            reference of the node or None if section name has no match
        """        

        return self.root.find_node(section_name)

    def remove_subsection_nodes(self):
        """Clean all the sub(sub)sections, only keeping the sections. 
        This is a operation for STORM default section writing step.
        """
        title_node = self.get_title_node()

        for section_node in title_node.children:
            section_node.children = []

        return True

    @classmethod
    def create_from_markdown(cls, topic: str, markdown: str):
        """Construct Article instance's markdown format.

        Args:
            markdown: article in markdown format string where section has hashtag (#)

        Returns:
            Article instance
        """

        article = cls(topic)
        article_node = ArticleNode.create_from_markdown(markdown)
        article.root.add_child(article_node)
        
        return article
    
