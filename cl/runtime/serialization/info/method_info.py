import inspect
from dataclasses import dataclass
from typing import Any
from typing import List
from typing import Optional
from typing import Type
from typing import get_type_hints
from cl.runtime.records.dataclasses_extensions import field


@dataclass
class MethodArgumentInfo:
    """Method argument information class."""

    name: Optional[str] = field()
    """Argument name."""

    type: Optional[Type] = field()
    """Argument type."""

    default: Optional[Any] = field()
    """Argument default value."""

    optional: Optional[bool] = field()
    """Argument is optional flag."""


@dataclass
class MethodInfo:
    """Method information class."""

    method_name: Optional[str] = field()
    """Method name."""

    label: Optional[str] = field()
    """Method label added by label decorator."""

    is_cl_viewer: Optional[bool] = field()
    """Method is viewer flag. True if method is decorated by viewer."""

    is_cl_process: Optional[bool] = field()
    """Method is process flag. True if method is decorated by process."""

    is_cl_handler: Optional[bool] = field()
    """Method is handler flag. True if method is decorated by handler."""

    is_cl_content: Optional[bool] = field()
    """Method is content flag. True if method is decorated by content."""

    is_abstract: Optional[bool] = field()
    """Method is abstract flag."""

    is_static: Optional[bool] = field()
    """Method is static flag."""

    docstring: Optional[str] = field()
    """Method docstring."""

    return_type: Optional[type] = field()
    """Method return type."""

    arguments: Optional[List[MethodArgumentInfo]] = field()
    """List of method arguments info."""

    def __init__(self, type_: Type, method_name: str):
        """Extract type method information."""

        self.method_name = method_name
        method = getattr(type_, method_name, None)

        if method is None:
            raise ValueError(f"Type {type_.__name__} does not have method {method_name}")

        # added by handler decorator
        self.label = method.__dict__.get("_label", None)

        # added by viewer decorator
        self.is_cl_viewer = hasattr(method, "_cl_viewer")

        # added by process decorator
        self.is_cl_process = hasattr(method, "_cl_process")

        # added by handler decorator
        self.is_cl_handler = hasattr(method, "_cl_handler")

        self.is_cl_content = hasattr(method, "_cl_content")

        self.is_abstract = getattr(method, "__isabstractmethod__", False)
        self.is_static = isinstance(inspect.getattr_static(type_, method_name), staticmethod)

        self.docstring = getattr(method, "__doc__")
        method_hints = get_type_hints(method)
        self.return_type = method_hints.get("return", inspect.Signature.empty)

        method_arguments = inspect.signature(method)

        self.arguments = [
            MethodArgumentInfo(
                name=parameter.name,
                type=method_hints.get(parameter.name, inspect.Parameter.empty),
                default=parameter.default,
                optional=parameter.default is not inspect.Parameter.empty and parameter.default is None,
            )
            for parameter in method_arguments.parameters.values()
            if parameter.name != "self"
        ]
