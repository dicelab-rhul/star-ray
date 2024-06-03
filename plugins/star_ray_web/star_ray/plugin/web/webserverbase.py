from typing import List, Dict, Any
import pathlib
import uvicorn
from fastapi import FastAPI, Path, Request
from deepmerge import always_merger
from star_ray.utils import ValidatedTemplates, ValidatedEnvironment


class WebServerBase:

    def __init__(
        self,
        namespace: str,
        path: str | List[str],
        package_name: str = None,
    ):
        super().__init__()
        self.app = FastAPI()
        self._templates = ValidatedTemplates()
        self._default_namespace = namespace
        # register the default namespace (other than star_ray)
        self.register_namespace(namespace, path, package_name=package_name)
        self.register_namespace(
            "star_ray", "plugin/web/static/", package_name="star_ray"
        )
        self.register_routes()
        # locate index path in the default namespace
        self._index = self._locate_index(self._default_namespace)
        self._context = dict()

    def _locate_index(self, namespace):
        index_candidates = self._templates.loader.list_templates_in_namespace(namespace)
        index_candidates = list(
            filter(lambda x: x.startswith("index"), index_candidates)
        )
        if not index_candidates:
            raise FileNotFoundError(
                f"Failed to locate index file in namespace {namespace}"
            )
        elif len(index_candidates) > 1:
            raise ValueError(
                f"Found multiple index files in namespace {namespace}: {index_candidates}"
            )
        return f"{namespace}/{index_candidates[0]}"

    def register_namespace(
        self, namespace: str, path: str | List[str], package_name: str = None
    ):
        self._templates.add_namespace(namespace, path=path, package_name=package_name)

    def register_routes(self):
        self.app.get("/")(self.serve_index)
        self.app.get("/static/{namespace}/{filename}")(self.serve_template)

    async def serve_index(self, request: Request):
        context = self._context.get(self._index, {})
        assert not "request" in context  # request is reserved
        context["request"] = request
        return self._templates.TemplateResponse(
            name=self._index, context={"request": request}
        )

    async def serve_template(
        self, request: Request, namespace: str = Path(...), filename: str = Path(...)
    ):
        _, suffix = ValidatedEnvironment.split_name_suffix(filename)
        media_type = None
        # TODO a proper mapping here
        if "js" in suffix:
            media_type = "application/javascript"
        name = f"{namespace}/{filename}"
        return self._templates.TemplateResponse(
            request=request,
            name=name,
            context=self.get_context(name),
            media_type=media_type,
        )

    def set_context(self, path: str, context: Dict[str, Any]):
        self._context[path] = context

    def update_context(self, path: str, context: Dict[str, Any]):
        return always_merger.merge(self._context.get(path, dict()), context)

    def get_context(self, path: str):
        return self._context.get(path, dict())

    def get_namespaces(self) -> List[str]:
        return self._templates.loader.get_namespaces()


# STATIC_PATH = str(pathlib.Path(__file__).parent / "static")
# server = WebServer(namespace="test", path=STATIC_PATH)
# uvicorn.run(server.app, host="localhost", port=8888, log_level="info")
