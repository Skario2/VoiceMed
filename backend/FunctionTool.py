import inspect
import json
from typing import Union, get_args, get_origin

from backend.ocr.call_eps import *
class FunctionTool:
    """
    A wrapper of a function and its description for a
    ChatGPT-understandable tool.
    A FunctionTool object is callable and calls function it wraps.
    It also has the metadata member containing the description of
    the function as defined in its documentation. \n
    Example:
    >>> def fun(x: int) -> int:
    ...   '''Adds 1 to x
    ...   :param x: An integer
    ...   :return: an incremented x
    ...   '''
    ...   return x + 1
    >>> fun_tool = FunctionTool(fun)
    >>> fun_tool(5)
    6
    >>> (fun_tool.metadata['function']
    ... ['parameters']['properties']['x']['description'])
    'An integer'
    """

    @staticmethod
    def __metadata__(func: callable) -> dict:
        type_mapping = {
            "str": "string",
            "int": "integer",
            "float": "number",
            "bool": "boolean",
            "list": "array",
            "dict": "object",
        }

        def _get_type_name(annotation):
            if annotation == inspect.Parameter.empty:
                return "string"
            if getattr(
                annotation, "__name__", None
            ) and annotation.__name__.lower() not in ["optional", "union"]:
                return annotation.__name__.lower()
            if get_origin(annotation) is type(None):
                return "null"
            if get_origin(annotation) in [list, dict]:
                args = get_args(annotation)
                if get_origin(annotation) is list:
                    return {
                        "type": "array",
                        "items": _get_type_name(args[0]) if args else "string",
                    }
                if get_origin(annotation) is dict and len(args) == 2:
                    return {
                        "type": "object",
                        "additionalProperties": _get_type_name(args[1]),
                    }
            if get_origin(annotation) is Union:
                types = [
                    type_mapping.get(_get_type_name(arg))
                    for arg in get_args(annotation)
                    if arg is not type(None)
                ]
                return types if len(types) > 1 else types[0]
            return str(annotation).lower()

        def _get_object_properties(json_obj):
            if isinstance(json_obj, dict):
                return {
                    "type": "object",
                    "properties": {
                        key: _get_object_properties(value)
                        for key, value in json_obj.items()
                    },
                }
            if isinstance(json_obj, list):
                return {
                    "type": "array",
                    "items": _get_object_properties(json_obj[0]),
                }
            return {"type": type_mapping.get(json_obj)}
            # raise f"Undefined type {type(json_obj)}"

        def _extract_section(lines, start_tag):
            section = []
            capturing = False
            for line in lines:
                if start_tag and line.strip().lower().startswith(start_tag.lower()):
                    capturing = True
                    section.append(line.split(start_tag, 1)[1].strip())
                elif not start_tag and not line.strip().startswith(":") and line.strip():
                    capturing = True
                    section.append(line.strip())
                elif capturing and line.strip():
                    if line.strip().startswith(":") or line.strip().lower() == "examples:":
                        break
                    section.append(line.strip())
            return "\n".join(section)

        signature = inspect.signature(func)
        func_name = func.__name__

        if inspect.isclass(func):
            func = func.__init__

        docstring = inspect.getdoc(func) or "No description available"
        lines = docstring.splitlines()
        description = _extract_section(lines, "")
        returning = _extract_section(lines, ":return:")
        description = description + "\nThe function returns: " + returning

        parameters = {"type": "object", "properties": {}, "required": []}

        self = inspect.ismethod(func)

        for name, param in signature.parameters.items():
            if self:
                self = False
                continue

            param_type = _get_type_name(param.annotation)
            if isinstance(param_type, str):
                param_type = type_mapping.get(param_type, param_type)

            param_description = _extract_section(lines, f":param {name}:") or "No description available"
            explicit_type = _extract_section(lines, f":type {name}:")
            properties = None
            if explicit_type:
                try:
                    properties = _get_object_properties(
                        json.loads(explicit_type.strip())
                    )
                except Exception:
                    properties = None

            if properties:
                param_entry = properties
                param_entry["description"] = param_description
            else:
                param_entry = {
                    "type": param_type,
                    "description": param_description,
                }

            parameters["properties"][name] = param_entry

            if param.default == inspect.Parameter.empty:
                parameters["required"].append(name)

        schema = {
            "type": "function",
            "function": {
                "name": func_name,
                "description": description,
                "parameters": parameters,
            },
        }

        return schema

    def __init__(
        self: "FunctionTool", function: callable, metadata: dict | None = None
    ) -> None:
        """
        Creates a new function tool that can be used by OpenAI prompts.
        If metadata is not specified, the constructor
        creates the function using its documentation string.
        Example of use:
            metadata = {
                "type": "function",
                "function": {
                    "name": "get_n_day_weather_forecast",
                    "description": "Get an N-day weather forecast",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "The city and state,
                                                e.g. San Francisco, CA",
                            },
                            "format": {
                                "type": "string",
                                "enum": ["celsius", "fahrenheit"],
                                "description": "The temperature unit to use.
                                 Infer this from the users location.",
                            },
                            "num_days": {
                                "type": "integer",
                                "description": "Number of days to forecast",
                            }
                        },
                        "required": ["location", "format", "num_days"]
                    },
                }
            }
            FunctionTool(get_n_day_weather_forecast, metadata)
        :param self: The function tool object to create.
        :param function: The function whose parameters determines OpenAI.
        :param metadata: The metadata of the function,
        including its description and its parameters.
        """
        self._function = function
        if metadata is None:
            self._metadata = FunctionTool.__metadata__(function)
        else:
            self._metadata = metadata

    def __call__(self, *args, **kwargs):
        return self._function(*args, **kwargs)

    @property
    def metadata(self):
        return self._metadata

    @property
    def function(self):
        return self._function


f = FunctionTool(put_info_from_voice)
print(f.metadata)