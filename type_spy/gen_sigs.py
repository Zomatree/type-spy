# SPDX-FileCopyrightText: 2023-present Zomatree <me@zomatree.live>
#
# SPDX-License-Identifier: MIT

import inspect
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
    Function,
    Signature,
    SignatureParameters,
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
) -> list[Function]:
    already_done = already_done or []
    parents = parents or []

    types: list[Function] = []

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

class Unknown:
    pass

def extract_signature(func: FunctionType, path: str) -> Function:
    name = func.__name__
    typevars: list[BaseTypeVar] = []

    sig = inspect.signature(func)
    pos_only = []
    params = []
    vargs = None
    kwargs = None
    kwarg_only = []

    for param in sig.parameters.values():
        ty = param.annotation if param.annotation is not inspect._empty else Unknown

        if param.kind is param.POSITIONAL_ONLY:
            pos_only.append(convert_type(param.annotation, typevars))

        elif param.kind is param.POSITIONAL_OR_KEYWORD:
            params.append(convert_type(param.annotation, typevars))

        elif param.kind is param.VAR_POSITIONAL:
            vargs = convert_type(param.annotation, typevars)

        elif param.kind is param.VAR_KEYWORD:
            kwargs = convert_type(param.annotation, typevars)

        elif param.kind is param.KEYWORD_ONLY:
            kwarg_only.append(convert_type(param.annotation, typevars))

    parameters = SignatureParameters(pos_only, params, vargs, kwarg_only, kwargs)
    signature = Signature(parameters, convert_type(sig.return_annotation, typevars))

    return Function(name, path, func.__doc__, MetaTypeVars(typevars), signature)

def convert_type(ty: Any, typevars: list[BaseTypeVar]) -> Type:
    args = get_args(ty)
    origin = get_origin(ty)

    if origin is typing.Union or origin is UnionType:
        return Union([convert_type(arg, typevars) for arg in args])

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
        return Signature(SignatureParameters([], [convert_type(ty, typevars) for ty in args[0]], None, [], None), convert_type(args[1], typevars))



    elif isinstance(ty, list):
        return List([convert_type(v, typevars) for v in ty])

    elif args:
        return Generic(
            convert_type(origin, typevars),
            [convert_type(arg, typevars) for arg in args],
        )

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
