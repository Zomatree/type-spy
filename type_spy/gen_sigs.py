# SPDX-FileCopyrightText: 2023-present Zomatree <me@zomatree.live>
#
# SPDX-License-Identifier: MIT

from ast import mod
from types import ModuleType, FunctionType, UnionType
from inspect import get_annotations
from typing import Iterator, get_args, get_origin, TypeVar as _TypeVar
import typing

from spec import Any
from .types import (
    Generic,
    Ident,
    List,
    MetaTypeVars,
    Parameter,
    Return,
    Root,
    Signature,
    Type,
    TypeVar,
    Union,
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
    parameters: list[Parameter] = []
    typevars: list[TypeVar] = []
    rt = Return(Ident("None"))

    for key, value in get_annotations(func).items():
        ty = convert_type(value, typevars)
        if key == "return":
            rt = Return(ty)
        else:
            parameters.append(Parameter(ty))

    return Root(name, path, func.__doc__, MetaTypeVars(typevars), Signature(parameters, rt))


def convert_type(ty: Any, typevars: list[TypeVar]) -> Type:
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
