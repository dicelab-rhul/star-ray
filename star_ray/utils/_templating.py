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
        kwargs.setdefault("normalize", True)
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
            validator = ValidatedEnvironment.get_validator(schema)
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
            context = ValidatedEnvironment._validate_context_with_schema(
                validator, context=context, normalize=True
            )
        elif context:
            # LOGGER.warning("Context file: %s was provided without a validation schema.", context_name)
            context = ValidatedEnvironment._validate_context_without_schema(context)
        else:
            context = dict()  # no configuration files were available
        globals = always_merger.merge(globals, context)
        # this will be used when the template is rendered (via `get_context`) to validate supplied context variables.

        return super().get_template(name, parent, globals)

    def validate_context(self, name: str, context: Mapping[str, Any]):
        validator = self._validator_cache.get(name, None)
        if validator:
            ValidatedEnvironment._validate_context_with_schema(
                validator, context=context, normalize=False
            )
        else:
            ValidatedEnvironment._validate_context_without_schema(context)

    @staticmethod
    def _validate_context_without_schema(context: Mapping[str, Any]):
        errors = ValidatedEnvironment._validate_context_keys(context)
        if errors:
            error_str = "\n    - ".join(errors)
            raise ValueError(f"Invalid context, see errors:\n    - {error_str}")
        return context

    @staticmethod
    def _validate_context_with_schema(
        validator: Any,
        context: MutableMapping[str, Any] = None,
        normalize: bool = True,
    ):
        if context is None:
            context = dict()
        if normalize:
            context = validator.normalized(context)  # set default values etc.
            if context is None:  # there were errors in normalization
                errors = ValidatedEnvironment._format_validator_errors(validator.errors)
                error_str = "\n    - ".join(errors)
                raise ValueError(
                    f"Context is not valid under the provided schema. See issues below:\n    - {error_str}"
                )
        if validator.validate(context):
            return context
        else:
            errors = ValidatedEnvironment._format_validator_errors(validator.errors)
            error_str = "\n    - ".join(errors)
            raise ValueError(
                f"Context is not valid under the provided schema. See issues below:\n    - {error_str}"
            )

    @staticmethod
    def _format_validator_errors(errors):
        result = []
        for k, errs in errors.items():
            for v in errs:
                if isinstance(v, dict):
                    result.extend(ValidatedEnvironment._format_validator_errors(v))
                elif isinstance(v, str):
                    result.append(f"Key: `{k}` {v}")
                else:
                    raise ValueError(
                        f"Internal error: unknown validation error type: {type(v)}"
                    )
        return result

    @staticmethod
    def get_validator(schema: MutableMapping[str, Any]) -> Validator:
        errors = ValidatedEnvironment._validate_schema(schema)
        if errors:
            error_str = "\n    - ".join(errors)
            raise ValueError(f"Invalid schema, see errors:\n    - {error_str}")
        return ValidatedEnvironment.validator_class(
            schema, normalize=True, allow_unknown=ValidatedEnvironment.allow_unknown
        )

    @staticmethod
    def load_and_validate_context(schema_path: str, context_path: str = None):
        schema_path = str(Path(schema_path).expanduser().resolve())
        with open(schema_path, "r", encoding="utf-8") as f:
            validator = ValidatedEnvironment.get_validator(json.load(f))
        context = None
        if context_path:
            with open(context_path, "r", encoding="utf-8") as f:
                context = json.load(f)
        return ValidatedEnvironment._validate_context_with_schema(
            validator,
            context=context,
            normalize=True,
        )

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
            if isinstance(rules, dict):
                if rules.get("type", None) == "dict":
                    # default must be specified in the nested definition
                    errors.extend(ValidatedEnvironment._validate_context_keys(schema))
                    sub_schema = rules.get("schema", None)
                    if sub_schema:
                        errors.extend(ValidatedEnvironment._validate_schema(sub_schema))
                    continue  # default isnt specified at the top level here...
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
