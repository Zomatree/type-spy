# SPDX-FileCopyrightText: 2023-present Zomatree <me@zomatree.live>
#
# SPDX-License-Identifier: MIT

from __future__ import annotations
from typing import TypeAlias

from spec import Any


class Generic:
    def __init__(self, ty: Type, generics: list[Type]):
        self.ty = ty
        self.generics = generics

    def __repr__(self):
        return f"{self.ty}[{', '.join(map(repr, self.generics))}]"

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.ty == other.ty and self.generics == other.generics


class Ident:
    def __init__(self, ty: str):
        self.ty = ty

    def __repr__(self):
        return self.ty

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.ty == other.ty


class List:
    def __init__(self, values: list[Type]) -> None:
        self.values = values

    def __repr__(self):
        return f"[{', '.join(map(repr, self.values))}]"

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.values == other.values


class TypeVar:
    def __init__(self, name: str) -> None:
        self.name = name

    def __repr__(self) -> str:
        return self.name

    def __eq__(self, other: Any):
        return isinstance(other, self.__class__) and self.name == other.name

    def __hash__(self):
        return hash(self.name)


class Union:
    def __init__(self, tys: list[Type]):
        self.tys = tys

    def __repr__(self):
        return " | ".join(map(repr, self.tys))

    def __eq__(self, other: Any):
        return isinstance(other, self.__class__) and self.tys == other.tys


Type: TypeAlias = Generic | Ident | List | TypeVar | Union


class Parameter:
    def __init__(self, ty: Type):
        self.ty = ty

    def __repr__(self):
        return repr(self.ty)

    def __eq__(self, other: Any):
        return isinstance(other, self.__class__) and self.ty == other.ty


class MetaTypeVars:
    def __init__(self, generics: list[TypeVar]):
        self.generics = generics

    def __repr__(self):
        return f"[{', '.join(map(repr, self.generics))}]"

    def __eq__(self, other: Any):
        return isinstance(other, self.__class__) and self.generics == other.generics


class Return:
    def __init__(self, ty: Type):
        self.ty = ty

    def __repr__(self):
        return repr(self.ty)

    def __eq__(self, other: Any):
        return isinstance(other, self.__class__) and self.ty == other.ty


class Signature:
    def __init__(self, parameters: list[Parameter], rt: Return):
        self.parameters = parameters
        self.rt = rt

    def __repr__(self):
        return f"({', '.join(map(repr, self.parameters))}) -> {self.rt!r}"

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
        self._parameters = remap_typevars(self.typevars.generics, self.signature.parameters)
        self._return = Return(remap_typevars(self.typevars.generics, [Parameter(self.signature.rt.ty)])[0].ty)

    def __repr__(self):
        return f"{self.typevars!r} {self.signature!r}"

    def __eq__(self, other: Any):
        return (
            isinstance(other, self.__class__)
            and self._parameters == other._parameters
            and self._return == other._return
        )


def remap_typevars(generics: list[TypeVar], parameters: list[Parameter]) -> list[Parameter]:
    typevar_map = {old: TypeVar(str(i)) for i, old in enumerate(generics)}

    return [Parameter(remap_types(typevar_map, param.ty)) for param in parameters]


def remap_types(typevar_map: dict[TypeVar, TypeVar], type: Type):
    if isinstance(type, Generic):
        return Generic(type.ty, [remap_types(typevar_map, arg) for arg in type.generics])

    elif isinstance(type, TypeVar):
        return typevar_map[type]

    elif isinstance(type, List):
        return List([remap_types(typevar_map, arg) for arg in type.values])

    elif isinstance(type, Union):
        return Union([remap_types(typevar_map, arg) for arg in type.tys])

    else:
        return type
