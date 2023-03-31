# SPDX-FileCopyrightText: 2023-present Zomatree <me@zomatree.live>
#
# SPDX-License-Identifier: MIT

from __future__ import annotations
from typing import cast

import lark

from .gen_sigs import *
from .types import *

l = lark.Lark(
    r"""
    ident: /\w+/
    generic: ident "[" type ("," type)* "]"

    typevar: /[a-zA-Z]+/
    typevartuple: "*" typevar
    paramspec: "**" typevar

    type_variable: typevar
        | typevartuple
        | paramspec

    list: "[" type ("," type)* "]"
    union: type ("|" type)+

    type: ident
        | generic
        | list
        | union
        | "(" signature ")"

    pos_only_params: type ("," type)* "," "/"
    params: type? ("," type)*
    vargs: "*" type
    kwargs: "**" type
    keyword_only_params: type? ("," type)*

    signature_parameters: "(" pos_only_params? params vargs? kwargs? keyword_only_params? ")"
    signature: signature_parameters ("->" type)?

    meta_type_variables: "[" type_variable ("," type_variable)* "]"

    start: meta_type_variables? signature

    %import common.WS
    %ignore WS
""",
    parser="lalr",
    start="start",
)


class SignatureTransformer(lark.Transformer):
    def typevar(self, tokens: list[lark.Token]):
        return TypeVar(tokens[0].value)

    def ident(self, tokens: list[lark.Token]) -> Ident:
        return Ident(tokens[0].value)

    def generic(self, tokens: list[Type]):
        return Generic(tokens[0], tokens[1:])

    def type(self, tokens: list[Type]):
        return tokens[0]

    def type_variable(self, tokens: list[TypeVariable]):
        return tokens[0]

    def signature_parameters(self, tokens: list[Type]):
        return tokens

    def parens(self, tokens: list[Type]):
        return tokens[0]

    def typevartuple(self, tokens: list[TypeVar]):
        return TypeVarTuple(tokens[0].name)

    def paramspec(self, tokens: list[TypeVar]):
        return ParamSpec(tokens[0].name)

    def union(self, tokens: list[Type]):
        return Union(tokens)

    def meta_type_variables(self, tokens: list[BaseTypeVar]):
        return MetaTypeVars(tokens)

    def signature(self, tokens: list[list[Type] | Type]):
        if tokens and isinstance(tokens[-1], Type):
            rt = tokens[-1]
            parameters = cast(list[Type], tokens[0])

        else:
            rt = Ident("None")
            parameters = cast(list[Type], tokens)

        return Signature(parameters, rt)

    def start(self, tokens: list[MetaTypeVars | Signature]):
        if isinstance(tokens[0], MetaTypeVars):
            typevars = tokens[0]
            sig = tokens[1]
        else:
            typevars = MetaTypeVars([])
            sig = tokens[0]

        assert isinstance(sig, Signature)

        return Root("<input>", "", "", typevars, sig)


def parse_signature(sig: str):
    tree = l.parse(sig)
    interp = SignatureTransformer()
    return interp.transform(tree)
