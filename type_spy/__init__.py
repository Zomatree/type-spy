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

    list: "[" type ("," type)* "]"

    type: ident
        | generic
        | list
        | union

    union: type ("|" type)+

    parameter: type
    return_ty: type

    signature: "(" parameter? ("," parameter)* ")" ("->" return_ty)?

    meta_generics: "[" typevar ("," typevar)* "]"

    start: meta_generics? signature

    %import common.WS
    %ignore WS
""",
    parser="lalr",
    start="start",
)


class SignatureTransformer(lark.Transformer):
    def typevar(self, tokens: list[lark.Token]):
        (token,) = tokens

        return TypeVar(token.value)

    def ident(self, tokens: list[lark.Token]) -> Ident:
        (token,) = tokens

        return Ident(token.value)

    def generic(self, tokens: list[Type]):
        return Generic(tokens[0], tokens[1:])

    def parameter(self, tokens: list[Type]):
        return Parameter(tokens[0])

    def type(self, tokens: list[Type]):
        return tokens[0]

    def return_ty(self, tokens: list[Type]):
        return Return(tokens[0])

    def union(self, tokens: list[Type]):
        return Union(tokens)

    def meta_generics(self, tokens: list[TypeVar]):
        return MetaTypeVars(tokens)

    def signature(self, tokens: list[Parameter | Return]):
        if tokens and isinstance(tokens[-1], Return):
            rt = tokens[-1]
            parameters = cast(list[Parameter], tokens[:-1])

        else:
            rt = Return(Ident("None"))
            parameters = cast(list[Parameter], tokens)

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
