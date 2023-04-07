import ast
from contextlib import contextmanager
from typing import Union as _Union, cast, TypeVar as _TypeVar

from .types import *

K = _TypeVar("K")
V = _TypeVar("V")

class Namespace(dict[K, V]):
    def __init__(self, name: str):
        self.name = name

Scopes = Namespace[str, _Union["Scopes", Value]]

class TypingModule(Namespace):
    TypeVar = TypeVar
    Callable = Signature

class NodeVisitor(ast.NodeVisitor):
    def __init__(self, name: str):
        super().__init__()
        self.attributes: dict[str, Value] = {}
        self.scopes: Scopes = Namespace(name)

        self.current_scopes: list[tuple[str, Scopes]] = []

    def add_to_current_scope(self, name: str, value: Value):
        self.current_scopes[-1][1][name] = value

    def get_from_current_scope(self, name: str) -> Value | Scopes:
        return self.current_scopes[-1][1][name]

    @contextmanager
    def enter_scope(self, name: str):
        try:
            parent_scope = self.current_scopes[-1][1]

            if name in parent_scope:
                scope = cast(Scopes, parent_scope[name])
            else:
                parent_scope[name] = scope = Namespace(name)

            self.current_scopes.append((name, scope))

            yield
        finally:
            self.current_scopes.pop()

    def visit_Assign(self, node: ast.Assign) -> Any:
        for target in node.targets:
            match target:
                case ast.Name(id):
                    self.add_to_current_scope(id, self.to_value(node.value))

    def visit_AugAssign(self, node: ast.AnnAssign) -> Any:
        match node.target:
            case ast.Name(id) if node.value:
                self.add_to_current_scope(id, self.to_value(node.value))

    def flatten_attribute(self, attr: ast.Attribute) -> Value | Namespace:
            attrs: list[str] = []

            expr: ast.expr = attr

            while isinstance(expr, ast.Attribute):
                attrs.append(expr.attr)
                expr = expr.value

            value = self.get_from_current_scope(attrs[-1])

            for attr_name in attrs[:-1]:
                if isinstance(value, Namespace):
                    value = value[attr_name]
                else:
                    raise Exception(f"Cannot get attribute of {attr_name} on {value} at {expr.lineno}")

            return value

    def to_value(self, expr: ast.expr) -> Value:
        match expr:
            case ast.Call():
                target = self.to_value(expr.func)

            case ast.Attribute:
                

    def to_type(self, expr: ast.expr | None, found_typevars: dict[str, BaseTypeVar]) -> Type:
        ...

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            if alias.name == "typing":
                self.scopes[alias.asname or alias.name] = TypingModule("typing")

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module != "typing":
            return

        for alias in node.names:
            try:
                self.scopes[alias.asname or alias.name] = getattr(TypingModule, alias.name)
            except AttributeError:
                print(f"ignoring: typing.{alias.name}")

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef, is_async: bool):
        found_typevars: dict[str, BaseTypeVar] = {}

        rt = self.to_type(node.returns, found_typevars) if node.returns else Ident("None")

        if is_async:
            rt = Generic(Ident("Coroutine"), [Ident("Any"), Ident("Any"), rt])

        parameters = node.args

        pos_only = [self.to_type(arg.annotation, found_typevars) for arg in parameters.posonlyargs]
        params = [self.to_type(arg.annotation, found_typevars) for arg in parameters.args]
        vargs = self.to_type(parameters.vararg.annotation, found_typevars) if parameters.vararg else self.to_type(None, found_typevars)
        kwarg_only = [self.to_type(arg.annotation, found_typevars) for arg in parameters.kwonlyargs]
        kwargs = self.to_type(parameters.kwarg.annotation, found_typevars) if parameters.kwarg else self.to_type(None, found_typevars)

        signature_parameters = SignatureParameters(pos_only, params, vargs, kwarg_only, kwargs)
        signature = Signature(signature_parameters, rt)
        func = Function(node.name, ".".join(scope[0] for scope in self.current_scopes), None, MetaTypeVars(list(found_typevars.values())), signature)

        self.add_to_current_scope(node.name, func)

        with self.enter_scope(node.name):
            for statement in node.body:
                self.visit(statement)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._visit_function(node, False)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._visit_function(node, True)

def parse_module(source: str, name: str) -> Module:
    tree = ast.parse(source, type_comments=True)

    visitor = NodeVisitor(name)
    visitor.visit(tree)

    return Module(name, visitor.collect())
