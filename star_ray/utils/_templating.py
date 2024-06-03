import json
import copy
import re

from pathlib import Path
from typing import (
    Any,
    Dict,
    List,
    Tuple,
    Mapping,
    MutableMapping,
    Sequence,
    Type,
    Literal,
    Callable,
    Optional,
    Union,
)
from jinja2 import (
    BytecodeCache,
    Environment,
    BaseLoader,
    PrefixLoader,
    PackageLoader,
    FileSystemLoader,
    Template,
    TemplateNotFound,
    Undefined,
    StrictUndefined,
)
from jinja2.runtime import Context
from jinja2.defaults import (
    BLOCK_END_STRING,
    BLOCK_START_STRING,
    COMMENT_END_STRING,
    COMMENT_START_STRING,
    KEEP_TRAILING_NEWLINE,
    LSTRIP_BLOCKS,
    TRIM_BLOCKS,
    VARIABLE_END_STRING,
    VARIABLE_START_STRING,
    LINE_STATEMENT_PREFIX,
    LINE_COMMENT_PREFIX,
    NEWLINE_SEQUENCE,
)
from jinja2.ext import Extension
from starlette.templating import Jinja2Templates


from deepmerge import always_merger
from cerberus import Validator as _Validator


__all__ = (
    "Validator",
    "TemplateLoader",
    "ValidatedTemplates",
    "ValidatedTemplate",
    "ValidatedEnvironment",
)


class Validator(_Validator):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._hex_color_pattern = re.compile(r"^#?[0-9a-fA-F]{6}$")

    def _validate_type_color(self, value):
        return not re.match(self._hex_color_pattern, value) is None

    def _validate_type_any(self, _):
        return True


class ValidatedTemplates(Jinja2Templates):

    def __init__(self):
        loader = TemplateLoader()
        ALLOW_REQUEST = {"request": {"type": "any", "default": ""}}
        env = ValidatedEnvironment(loader=loader, schema_globals=ALLOW_REQUEST)
        super().__init__(env=env)

    def add_namespace(
        self,
        namespace: str,
        path: str | List[str],
        package_name: str = None,
        follow_links: bool = False,
    ):
        self.loader.add_namespace(
            namespace, path, package_name=package_name, follow_links=follow_links
        )

    def TemplateResponse(self, *args, **kwargs):
        return super().TemplateResponse(*args, **kwargs)

    @property
    def loader(self) -> "TemplateLoader":
        loader = self.env.loader
        assert isinstance(loader, TemplateLoader)
        return loader


class ValidatedTemplate(Template):

    def new_context(
        self,
        vars: Optional[Dict[str, Any]] = None,
        shared: bool = False,
        locals: Optional[Mapping[str, Any]] = None,
    ) -> Context:
        assert isinstance(self.environment, ValidatedEnvironment)
        self.environment.validate_context(self.name, vars)
        return super().new_context(vars, shared, locals)


class ValidatedEnvironment(Environment):

    EXT_SCHEMA = ".schema.json"
    EXT_CONTEXT = ".json"

    allow_unknown = False
    validator_class = Validator
    template_class = ValidatedTemplate

    def __init__(
        self,
        block_start_string: str = BLOCK_START_STRING,
        block_end_string: str = BLOCK_END_STRING,
        variable_start_string: str = VARIABLE_START_STRING,
        variable_end_string: str = VARIABLE_END_STRING,
        comment_start_string: str = COMMENT_START_STRING,
        comment_end_string: str = COMMENT_END_STRING,
        line_statement_prefix: Optional[str] = LINE_STATEMENT_PREFIX,
        line_comment_prefix: Optional[str] = LINE_COMMENT_PREFIX,
        trim_blocks: bool = TRIM_BLOCKS,
        lstrip_blocks: bool = LSTRIP_BLOCKS,
        newline_sequence: Literal["\\n", "\\r\\n", "\\r"] = NEWLINE_SEQUENCE,
        keep_trailing_newline: bool = KEEP_TRAILING_NEWLINE,
        extensions: Sequence[Union[str, Type["Extension"]]] = (),
        optimized: bool = True,
        undefined: Type[
            Undefined
        ] = StrictUndefined,  # defaults to StrictUndefined now for better validation!
        finalize: Optional[Callable[..., Any]] = None,
        autoescape: Union[bool, Callable[[Optional[str]], bool]] = False,
        loader: Optional["BaseLoader"] = None,
        cache_size: int = 400,
        auto_reload: bool = True,
        bytecode_cache: Optional["BytecodeCache"] = None,
        enable_async: bool = False,
        schema_globals: Mapping[str, Any] = None,
    ):
        super().__init__(
            block_start_string,
            block_end_string,
            variable_start_string,
            variable_end_string,
            comment_start_string,
            comment_end_string,
            line_statement_prefix,
            line_comment_prefix,
            trim_blocks,
            lstrip_blocks,
            newline_sequence,
            keep_trailing_newline,
            extensions,
            optimized,
            undefined,
            finalize,
            autoescape,
            loader,
            cache_size,
            auto_reload,
            bytecode_cache,
            enable_async,
        )
        self._schema_globals = schema_globals if schema_globals else dict()
        self._validator_cache = dict()

    def get_template(
        self,
        name: str | Template,
        parent: str | None = None,
        globals: MutableMapping[str, Any] | None = None,
    ) -> Template:
        if name not in self._validator_cache:
            self._validator_cache[name] = None

        filename, _ = ValidatedEnvironment.split_name_suffix(name)
        # check for configuration files with the same name
        context_name = filename.with_suffix(ValidatedEnvironment.EXT_CONTEXT)
        schema_name = filename.with_suffix(ValidatedEnvironment.EXT_SCHEMA)
        try:
            schema = json.loads(
                super().get_template(str(schema_name), None, {}).render()
            )
            schema = always_merger.merge(copy.deepcopy(self._schema_globals), schema)
            validator = self.get_validator(schema)
            self._validator_cache[name] = validator
        except TemplateNotFound:
            schema = None
        try:
            context = json.loads(
                super().get_template(str(context_name), None, {}).render()
            )
        except TemplateNotFound:
            context = None

        if schema:
            context = self._validate_context_with_schema(
                validator, context=context, normalize=True
            )
        elif context:
            # LOGGER.warning("Context file: %s was provided without a validation schema.", context_name)
            context = self._validate_context_without_schema(context)
        else:
            context = dict()  # no configuration files were available
        globals = always_merger.merge(globals, context)
        # this will be used when the template is rendered (via `get_context`) to validate supplied context variables.

        return super().get_template(name, parent, globals)

    def validate_context(self, name: str, context: Mapping[str, Any]):
        validator = self._validator_cache.get(name, None)
        if validator:
            self._validate_context_with_schema(validator, context, normalize=False)
        else:
            self._validate_context_without_schema(context)

    def _validate_context_without_schema(self, context: Mapping[str, Any]):
        errors = ValidatedEnvironment._validate_context_keys(context)
        if errors:
            error_str = "\n    - ".join(errors)
            raise ValueError(f"Invalid context, see errors:\n    - {error_str}")
        return context

    def _validate_context_with_schema(
        self,
        validator: Any,
        context: MutableMapping[str, Any] = None,
        normalize: bool = False,
    ):
        if context is None:
            context = dict()
        if normalize:
            context = validator.normalized(context)  # set default values etc.
        if validator.validate(context):
            return context
        else:
            errors = []
            for k, errs in validator.errors.items():
                for v in errs:
                    errors.append(f"Key: `{k}` {v}")
            error_str = "\n    - ".join(errors)
            raise ValueError(
                f"Context is not valid under the provided schema. see issues below:\n    - {error_str}"
            )

    def get_validator(self, schema: MutableMapping[str, Any]) -> Validator:
        errors = ValidatedEnvironment._validate_schema(schema)
        if errors:
            error_str = "\n    - ".join(errors)
            raise ValueError(f"Invalid schema, see errors:\n    - {error_str}")
        return self.validator_class(schema, allow_unknown=self.allow_unknown)

    @staticmethod
    def split_name_suffix(file: str):
        filename = Path(file).name
        parent = Path(file).parent
        name, *suffix = filename.split(".")
        return parent / name, suffix

    @staticmethod
    def _validate_context_keys(context: MutableMapping[str, Any]):
        errors = []
        for key, _ in context.items():
            # TODO check that the key follows jinja variable syntax
            if "-" in key:
                errors.append(f"Invalid character '-' found in context key: '{key}'.")
        return errors

    @staticmethod
    def _validate_schema(schema: MutableMapping[str, Any]):
        errors = []
        errors.extend(ValidatedEnvironment._validate_context_keys(schema))
        for key, rules in schema.items():
            # Check if default value is set
            if "default" not in rules:
                errors.append(f"No default value specified for field: '{key}'")
        return errors


class TemplateLoader(BaseLoader):

    def __init__(self):
        super().__init__()
        self._prefix_loader = PrefixLoader({})

    def add_namespace(
        self,
        namespace: str,
        path: str | List[str],
        *args,
        package_name: str = None,
        follow_links: bool = False,
        **kwargs,
    ):
        if package_name:
            self._prefix_loader.mapping[namespace] = PackageLoader(
                package_name, package_path=path
            )
        else:
            self._prefix_loader.mapping[namespace] = FileSystemLoader(
                path, followlinks=follow_links
            )

    def get_loader(self, namespace: str) -> Tuple[BaseLoader, str]:
        return self._prefix_loader.get_loader(namespace + "/")[0]

    def get_namespaces(self) -> List[str]:
        return list(self._prefix_loader.mapping.keys())

    def list_templates_in_namespace(self, namespace) -> List[str]:
        return self._prefix_loader.get_loader(namespace + "/")[0].list_templates()

    def list_templates(self) -> List[str]:
        return self._prefix_loader.list_templates()

    def get_source(self, environment, template):
        return self._prefix_loader.get_source(environment, template)


# if __name__ == "__main__":
#     dir = "/home/ben/Documents/repos/dicelab/icua2/icua2/test/test_multitask_loader/svg_template/"

#     templates = Templates()
#     templates.add_namespace("test", dir)

#     from starlette.requests import Request
#     from starlette.datastructures import URL

#     # Create a request scope dictionary
#     request_scope = {
#         "type": "http",
#         "method": "GET",
#         "path": "/your-path",
#         "query_string": b"",
#         "headers": [],
#         "scheme": "http",
#         "server": ("example.com", 80),
#         "client": ("127.0.0.1", 12345),
#         "url": URL("http://example.com/your-path"),
#     }
#     stub_request = Request(scope=request_scope)
#     context = {
#         "task_name": "task",
#         "x": 10,
#         "y": 10,
#         "radius": 10,
#         "width": 100,
#         "height": 100,
#         "stroke_color": "#ffffff",
#         "stroke": 2,
#         "color": "#000000",
#     }
#     print(
#         templates.TemplateResponse(
#             name="test/task.svg.jinja",
#             request=stub_request,
#             context={"task_name": "fooo"},
#         ).body
#     )
