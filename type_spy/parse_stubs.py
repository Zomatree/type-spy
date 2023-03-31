import ast

from .types import *

class Transformer(ast.NodeTransformer):
    def visit_Name(self, node: ast.Name) -> Any:
        return Ident(node.id)

def parse_source(source: str) -> list[Signature]:
    tree = ast.parse(source, type_comments=True)


