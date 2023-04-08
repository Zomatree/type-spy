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
    def __init__(self, pos_only: list[Type], params: list[Type], vargs: Type | None, kwarg_only: list[Type], kwargs: Type | None) -> None:
        self.pos_only = pos_only
        self.params = params
        self.vargs = vargs
        self.kwarg_only = kwarg_only
        self.kwargs = kwargs

    def __eq__(self, other: Any):
        return isinstance(other, self.__class__) and self.pos_only == other.pos_only and self.params == other.params and self.vargs == other.vargs and self.kwargs == other.kwargs and self.kwarg_only == other.kwarg_only

    def __repr__(self):
        parts: list[str] = []

        if pos_only := self.pos_only:
            for arg in pos_only:
                parts.append(repr(arg))

            parts.append("/")

        parts.extend(map(repr, self.params))

        if vargs := self.vargs:
            parts.append(f"*{vargs!r}")

        if not self.vargs and self.kwarg_only:
            parts.append("*")

        parts.extend(map(repr, self.kwarg_only))

        if kwargs := self.kwargs:
            parts.append(f"**{kwargs!r}")

        return ", ".join(parts)

class Signature:
    def __init__(self, parameters: SignatureParameters, rt: Type):
        self.parameters = parameters
        self.rt = rt

    def __repr__(self):
        return f"({self.parameters!r}) -> {self.rt!r}"

    def __eq__(self, other: Any):
        return isinstance(other, self.__class__) and self.parameters == other.parameters


class Function:
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

        typevar_map = {old: old.__class__(str(i)) for i, old in enumerate(self.typevars.generics)}

        self._parameters = normalize_typevars(typevar_map, self.signature.parameters)
        self._return = remap_types(typevar_map, self.signature.rt)

    def __repr__(self):
        return f"{self.typevars!r} {self.signature!r}"

    def __eq__(self, other: Any):
        return (
            isinstance(other, self.__class__)
            and self._parameters == other._parameters
            and self._return == other._return
        )

Value = Function | TypeVar | None

class Module:
    def __init__(self, name: str, attributes: dict[str, Value]):
        self.name = name
        self.attributes = attributes

def normalize_typevars(typevar_map: dict[BaseTypeVar, BaseTypeVar], parameters: SignatureParameters) -> SignatureParameters:

    return SignatureParameters(
        [remap_types(typevar_map, param) for param in parameters.pos_only],
        [remap_types(typevar_map, param) for param in parameters.params],
        remap_types(typevar_map, parameters.vargs) if parameters.vargs else None,
        [remap_types(typevar_map, param) for param in parameters.kwarg_only],
        remap_types(typevar_map, parameters.kwargs) if parameters.kwargs else None
    )


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
            return Signature(normalize_typevars(typevar_map, type.parameters), remap_types(typevar_map, type.rt))

        case Ident():
            for k, v in typevar_map.items():
                if k.name == type.ty:
                    return v

            return type
