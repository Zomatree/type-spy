# SPDX-FileCopyrightText: 2023-present Zomatree <me@zomatree.live>
#
# SPDX-License-Identifier: MIT

from types import ModuleType, FunctionType, UnionType
from inspect import get_annotations
from typing import Iterator, get_args, get_origin, TypeVar as _TypeVar, ParamSpec as _ParamSpec, TypeVarTuple as _TypeVarTuple, Callable as _Callable, Any
import typing

from .types import (
    BaseTypeVar,
    Generic,
    Ident,
    List,
    MetaTypeVars,
    ParamSpec,
    Root,
    Signature,
    Type,
    TypeVar,
    Union,
    TypeVarTuple
)

__all__ = ("convert_module", "extract_signature", "convert_type", "find_matching")


def convert_module(
    module: ModuleType,
    already_done: list[ModuleType] | None = None,
    parents: list[ModuleType] | None = None,
) -> list[Root]:
    already_done = already_done or []
    parents = parents or []

    types: list[Root] = []

    for key in dir(module):
        if key.startswith("_"):  # attempt to remove private stuff
            continue

        value = getattr(module, key)

        if isinstance(value, ModuleType):
            if value.__package__ != module.__package__:
                continue

            if value in already_done:
                continue

            already_done.append(value)

            types.extend(convert_module(value, already_done, parents + [module]))

        elif isinstance(value, FunctionType):
            types.append(extract_signature(value, ".".join([parent.__name__ for parent in parents])))

    return types


def extract_signature(func: FunctionType, path: str) -> Root:
    name = func.__name__
    parameters: list[Type] = []
    typevars: list[BaseTypeVar] = []
    rt = Ident("None")

    for key, value in get_annotations(func, eval_str=True).items():
        ty = convert_type(value, typevars)
        if key == "return":
            rt = ty
        else:
            parameters.append(ty)

    return Root(name, path, func.__doc__, MetaTypeVars(typevars), Signature(parameters, rt))


def convert_type(ty: Any, typevars: list[BaseTypeVar]) -> Type:
    args = get_args(ty)
    origin = get_origin(ty)

    if origin is typing.Union or origin is UnionType:
        return Union([convert_type(arg, typevars) for arg in args])

    elif args:
        return Generic(
            convert_type(origin, typevars),
            [convert_type(arg, typevars) for arg in args],
        )

    elif isinstance(ty, _TypeVar):
        tv = TypeVar(ty.__name__)

        if tv not in typevars:
            typevars.append(tv)

        return tv

    elif isinstance(ty, _ParamSpec):
        ps = ParamSpec(ty.__name__)

        if ps not in typevars:
            typevars.append(ps)

        return ps

    elif isinstance(ty, _TypeVarTuple):
        tvt = TypeVarTuple(ty.__name__)

        if tvt not in typevars:
            typevars.append(tvt)

        return tvt

    elif isinstance(ty, _Callable):
        return Signature([convert_type(p, typevars) for p in args[0]], convert_type(args[1], typevars))

    elif isinstance(ty, list):
        return List([convert_type(v, typevars) for v in ty])

    else:
        if ty is None:
            return Ident("None")

        if isinstance(ty, str):
            return Ident(ty)

        try:
            return Ident(ty.__name__)
        except:
            return Ident("Unknown")


T = _TypeVar("T")


def find_matching(iterator: Iterator[T], value: T) -> Iterator[T]:
    return filter(lambda v: v == value, iterator)
