import sys
import json
import pathlib
import pkgutil

from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from japiter import JAPIRouter


INDEX_HTML = """\
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>RetroLab - Notebook</title>
  <link rel="icon" type="image/x-icon" href="/static/favicons/favicon-notebook.ico" class="favicon">
</head>
<body>
  <script id="jupyter-config-data" type="application/json">
    PAGE_CONFIG
  </script>
  <script src="/static/retro/bundle.js" main="index"></script>
  <script type="text/javascript">
    /* Remove token from URL. */
    (function () {
      var parsedUrl = new URL(window.location.href);
      if (parsedUrl.searchParams.get('token')) {
        parsedUrl.searchParams.delete('token');
        window.history.replaceState({ }, '', parsedUrl.href);
      }
    })();
  </script>
</body>
</html>
"""


class RetroLabRouter(JAPIRouter):
    def init(self, japiter):
        self.japiter = japiter
        self.kernelspecs = {}
        self.sessions = {}
        self.kernels = {}

        retrolab_package = pkgutil.get_loader("retrolab")
        self.retrolab_dir = pathlib.Path(retrolab_package.path).parent
        self.prefix_dir = pathlib.Path(sys.prefix)

        self.japiter.app.mount(
            "/static/retro",
            StaticFiles(directory=self.retrolab_dir / "static"),
            name="static",
        )
        self.japiter.app.mount(
            "/lab/extensions/@retrolab/lab-extension/static",
            StaticFiles(directory=self.retrolab_dir / "labextension" / "static"),
            name="labextension/static",
        )
        self.japiter.app.mount(
            "/lab/api/themes",
            StaticFiles(
                directory=self.prefix_dir / "share" / "jupyter" / "lab" / "themes"
            ),
            name="themes",
        )
        self.japiter.app.include_router(router)


router = RetroLabRouter()


@router.get("/")
async def _():
    return RedirectResponse(
        f"http://{router.japiter.host}:{router.japiter.port}/retro/notebooks/Untitled.ipynb"
    )


@router.get("/retro/notebooks/{name}", response_class=HTMLResponse)
async def _():
    for path in (router.retrolab_dir / "labextension" / "static").glob(
        "remoteEntry.*.js"
    ):
        load = f"static/{path.name}"
        break

    page_config = {
        "appName": "RetroLab",
        "appNamespace": "retro",
        "appSettingsDir": str(
            router.prefix_dir / "share" / "jupyter" / "lab" / "settings"
        ),
        "appUrl": "/lab",
        "appVersion": "0.2.2",
        "baseUrl": "/",
        "cacheFiles": True,
        "disabledExtensions": [],
        "extraLabextensionsPath": [],
        "federated_extensions": [
            {
                "extension": "./extension",
                "load": load,
                "name": "@retrolab/lab-extension",
                "style": "./style",
            }
        ],
        "frontendUrl": "/retro/",
        "fullAppUrl": "/lab",
        "fullLabextensionsUrl": "/lab/extensions",
        "fullLicensesUrl": "/lab/api/licenses",
        "fullListingsUrl": "/lab/api/listings",
        "fullMathjaxUrl": "/static/notebook/components/MathJax/MathJax.js",
        "fullSettingsUrl": "/lab/api/settings",
        "fullStaticUrl": "/static/retro",
        "fullThemesUrl": "/lab/api/themes",
        "fullTranslationsApiUrl": "/lab/api/translations",
        "fullTreeUrl": "/lab/tree",
        "fullWorkspacesApiUrl": "/lab/api/workspaces",
        "labextensionsPath": [
            str(router.prefix_dir / "share" / "jupyter" / "labextensions")
        ],
        "labextensionsUrl": "/lab/extensions",
        "licensesUrl": "/lab/api/licenses",
        "listingsUrl": "/lab/api/listings",
        "mathjaxConfig": "TeX-AMS-MML_HTMLorMML-full,Safe",
        "retroLogo": False,
        "retroPage": "notebooks",
        "schemasDir": str(router.prefix_dir / "share" / "jupyter" / "lab" / "schemas"),
        "settingsUrl": "/lab/api/settings",
        "staticDir": str(router.retrolab_dir / "static"),
        "templatesDir": str(router.retrolab_dir / "templates"),
        "terminalsAvailable": True,
        "themesDir": str(router.prefix_dir / "share" / "jupyter" / "lab" / "themes"),
        "themesUrl": "/lab/api/themes",
        "translationsApiUrl": "/lab/api/translations",
        "treeUrl": "/lab/tree",
        "workspacesApiUrl": "/lab/api/workspaces",
        "wsUrl": "",
    }
    index = INDEX_HTML.replace("PAGE_CONFIG", json.dumps(page_config))
    return index


@router.get("/api/terminals")
async def _():
    return []


@router.get("/lab/api/settings/@jupyterlab/{name0}:{name1}")
async def _(name0, name1):
    with open(
        router.prefix_dir
        / "share"
        / "jupyter"
        / "lab"
        / "schemas"
        / "@jupyterlab"
        / name0
        / f"{name1}.json"
    ) as f:
        schema = json.load(f)
    return {
        "id": f"@jupyterlab/{name0}:plugin",
        "schema": schema,
        "version": "3.1.0-rc.1",
        "raw": "{}",
        "settings": {},
        "last_modified": None,
        "created": None,
    }


@router.get("/api/contents/{name}")
async def _(name):
    with open(name) as f:
        content = json.load(f)
    return {
        "name": name,
        "path": name,
        "last_modified": "2021-07-22T09:24:05.346859Z",
        "created": "2021-07-22T09:24:05.346859Z",
        "content": content,
        "format": "json",
        "mimetype": None,
        "size": 72,
        "writable": True,
        "type": "notebook",
    }


@router.get("/api/contents/{name}/checkpoints")
async def _(name):
    return [{"id": "checkpoint", "last_modified": "2021-07-22T13:46:20.363250Z"}]


@router.get("/lab/api/settings")
async def _():
    settings = []
    for path in (
        router.prefix_dir / "share" / "jupyter" / "lab" / "schemas" / "@jupyterlab"
    ).glob("*/*.json"):
        with open(path) as f:
            schema = json.load(f)
        setting = {
            "id": f"@jupyterlab/{path.parent.name}:{path.stem}",
            "schema": schema,
            "version": "3.1.0-rc.1",
            "raw": "{}",
            "settings": {},
            "warning": None,
            "last_modified": None,
            "created": None,
        }
        settings.append(setting)
    return {"settings": settings}


def init(japiter):
    router.init(japiter)
    return router
