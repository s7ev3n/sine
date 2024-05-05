from typing import Dict, List, Optional, Union
from abc import ABC, abstractclassmethod


class ArticleSection:
    """(Sub)Section of the article."""

    def __init__(self, section_name: str, content=None) -> None:
        self.section_name = section_name
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
    def __init__(self, topic_name):
        self.root = ArticleSection(topic_name)
    
    def get_outline_tree(self):

        def build_tree(node) -> Dict[str, Dict]:
            tree = {}
            for child in node.children:
                tree[child.section_name] = build_tree(child)
            
            return tree if tree else {}
        
        return build_tree(self.root)
    
    def get_first_level_section_names(self) -> List[str]:
        """Get first level section names of the article."""
        
        return [i.section_name for i in self.root.children]

    def to_string(self):
        """export article to string."""
        pass

    @classmethod
    def create_article_from_string(cls, topic_name: str, article_text: str):
        """create article object from string."""
        pass