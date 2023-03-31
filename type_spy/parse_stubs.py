import ast

from .types import *

class Function:
    pass

Value = Function

class Transformer(ast.NodeVisitor):
    def __init__(self):
        super().__init__()
        self.imports: dict[str, str] = {}
        self.imports_from: dict[str, dict[str, str]] = {}
        self.attributes: dict[str, Value] = {}

    def to_type(self, expr: ast.expr) -> Type:
        ...

    def visit_Import(self, node: ast.Import):
        for name in node.names:
            self.imports[name.asname or name.name] = name.name

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if (mod_name := node.module) is None:
            return  # dont need to care - yet

        module = self.imports_from.setdefault(mod_name, {})

        for name in node.names:
            module[name.asname or name.name] = name.name

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef, is_async: bool):
        rt = self.to_type(node.returns) if node.returns else Ident("None")

        if is_async:
            rt = Generic(Ident("Coroutine"), [Ident("Any"), Ident("Any"), rt])



    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._visit_function(node, False)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._visit_function(node, True)

def parse_source(source: str) -> list[Signature]:
    tree = ast.parse(source, type_comments=True)

    Transformer().visit(tree)
