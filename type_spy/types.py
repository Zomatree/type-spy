# SPDX-FileCopyrightText: 2023-present Zomatree <me@zomatree.live>
#
# SPDX-License-Identifier: MIT

from __future__ import annotations
from typing import Literal, TypeAlias, Union as _Union, Any


class Generic:
    def __init__(self, ty: Type, generics: list[Type]):
        self.ty = ty
        self.generics = generics

    def __repr__(self):
        return f"{self.ty}[{', '.join(map(repr, self.generics))}]"

    def __eq__(self, other: Any):
        return isinstance(other, self.__class__) and self.ty == other.ty and self.generics == other.generics


class Ident:
    def __init__(self, ty: str):
        self.ty = ty

    def __repr__(self):
        return self.ty

    def __eq__(self, other: Any):
        return isinstance(other, self.__class__) and self.ty == other.ty


class List:
    def __init__(self, values: list[Type]) -> None:
        self.values = values

    def __repr__(self):
        return f"[{', '.join(map(repr, self.values))}]"

    def __eq__(self, other: Any):
        return isinstance(other, self.__class__) and self.values == other.values


class BaseTypeVar:
    def __init__(self, name: str) -> None:
        self.name = name

    def __repr__(self) -> str:
        return self.name

    def __eq__(self, other: Any):
        return isinstance(other, self.__class__) and self.name == other.name

    def __hash__(self):
        return hash(self.name)

class TypeVar(BaseTypeVar):
    pass

class TypeVarTuple(BaseTypeVar):
    def __repr__(self):
        return f"*{self.name}"

class ParamSpec(BaseTypeVar):
    def __repr__(self):
        return f"**{self.name}"

class Union:
    def __init__(self, tys: list[Type]):
        self.tys = tys

    def __repr__(self):
        return " | ".join(map(repr, self.tys))

    def __eq__(self, other: Any):
        return isinstance(other, self.__class__) and self.tys == other.tys

TypeVariable: TypeAlias = TypeVar | TypeVarTuple | ParamSpec
Type: TypeAlias = _Union[Generic, Ident, List, BaseTypeVar, Union, "Signature"]
Parameters = (tuple[Literal["pos_only"], list[Type]]
    | tuple[Literal["params"], list[Type]]
    | tuple[Literal["vargs"], Type]
    | tuple[Literal["kwargs"], Type]
    | tuple[Literal["keyword_only"], Type]
)

class MetaTypeVars:
    def __init__(self, generics: list[BaseTypeVar]):
        self.generics = generics

    def __repr__(self):
        return f"[{', '.join(map(repr, self.generics))}]"

    def __eq__(self, other: Any):
        return isinstance(other, self.__class__) and self.generics == other.generics

class SignatureParameters:
    def __init__(self, pos_only: list[Type], params: list[Type], vargs: Type | None, kwargs: Type | None, kwarg_only: list[Type]) -> None:
        self.pos_only = pos_only
        self.params = params
        self.vargs = vargs
        self.kwargs = kwargs
        self.kwarg_only = kwarg_only

    def __eq__(self, other: Any):
        return isinstance(other, self.__class__) and self.pos_only == other.pos_only and self.params == other.params and self.vargs == other.vargs and self.kwargs == other.kwargs and self.kwarg_only == other.kwarg_only

    def __repr__(self):
        self.parts = []

        if 

class Signature:
    def __init__(self, parameters: SignatureParameters, rt: Type):
        self.parameters = parameters
        self.rt = rt

    def __repr__(self):
        return f"({self.parameters!r}) -> {self.rt!r}"

    def __eq__(self, other: Any):
        return isinstance(other, self.__class__) and self.parameters == other.parameters


class Root:
    def __init__(
        self,
        name: str,
        path: str,
        docstring: str | None,
        typevars: MetaTypeVars,
        signature: Signature,
    ) -> None:
        self.name = name
        self.path = path
        self.docstring = docstring
        self.typevars = typevars
        self.signature = signature
        self._parameters = normalize_typevars(self.typevars.generics, self.signature.parameters)
        self._return = normalize_typevars(self.typevars.generics, [self.signature.rt])[0]

    def __repr__(self):
        return f"{self.typevars!r} {self.signature!r}"

    def __eq__(self, other: Any):
        return (
            isinstance(other, self.__class__)
            and self._parameters == other._parameters
            and self._return == other._return
        )


def normalize_typevars(generics: list[BaseTypeVar], parameters: list[Type]) -> list[Type]:
    typevar_map = {old: old.__class__(str(i)) for i, old in enumerate(generics)}

    return [remap_types(typevar_map, param) for param in parameters]


def remap_types(typevar_map: dict[BaseTypeVar, BaseTypeVar], type: Type):
    match type:
        case Generic():
            return Generic(type.ty, [remap_types(typevar_map, arg) for arg in type.generics])

        case BaseTypeVar():
            return typevar_map[type]

        case List():
            return List([remap_types(typevar_map, arg) for arg in type.values])

        case Union():
            return Union([remap_types(typevar_map, arg) for arg in type.tys])

        case Signature():
            return Signature(
                [remap_types(typevar_map, arg) for arg in type.parameters],
                remap_types(typevar_map, type.rt)
            )

        case Ident():
            for k, v in typevar_map.items():
                if k.name == type.ty:
                    return v

            return type
