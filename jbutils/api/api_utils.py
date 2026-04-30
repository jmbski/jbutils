import argparse
import logging

from collections.abc import Callable

from argcomplete import autocomplete
from fastapi import FastAPI, APIRouter, Request
from fastapi.middleware.cors import CORSMiddleware

from jbutils import consts
from jbutils.models import GunicornApp
from jbutils.api.api_types import ApiHttpCallback, ApiLogger


def get_logger(name: str = "gunicorn.error") -> logging.Logger:
    return logging.getLogger(name)


def assemble_api(
    routers: list[APIRouter] | None = None,
    base_url: str = "/api/v1",
    http_callback: ApiHttpCallback | None = None,
) -> FastAPI:
    app = FastAPI()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if http_callback is not None:

        @app.middleware("http")
        async def apply_callback(request: Request, call_next):
            await http_callback(request, call_next)

    @app.get(f"{base_url}/health")
    def health():
        get_logger().info("Health works")

        return {"data": "Health worked"}

    if routers is not None:
        for router in routers:
            app.include_router(router)

    return app


def build_server(
    routers: list[APIRouter] | None = None,
    port: int = 7000,
    socket: str = "",
    opts: dict | None = None,
    local_callback: Callable[[bool], None] | None = None,
    http_callback: ApiHttpCallback | None = None,
) -> GunicornApp:
    app = assemble_api(routers, http_callback=http_callback)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--local", "-l", action="store_true", help="Run the server in local mode"
    )

    parser.add_argument(
        "--force-embed",
        "-f",
        action="store_true",
        help="If true, force embedding of default data",
    )
    parser.add_argument(
        "--port",
        "-p",
        type=int,
        help="Specify a particular port to run for the local server",
    )
    parser.add_argument(
        "--socket-name",
        "-s",
        help="Specify a socket name to use (do not include extension)",
    )

    autocomplete(parser)
    args = parser.parse_args()

    # TODO: add data embedding process outside of logcleaner package

    socket = args.socket_name or socket
    port = args.port or port

    bind = f"unix:/run/gunicorn/{socket}.sock"

    if args.local:
        if local_callback is not None:
            local_callback(True)
        bind = f"127.0.0.1:{port}"
        print(f"Running in local mode at: '{bind}'")

    options = {
        "bind": bind,
        "workers": 4,
        "worker_class": "uvicorn.workers.UvicornWorker",
        "loglevel": "info",
        "keepalive": 10,
        "max_requests": 0,
        "preload_app": False,
        "umask": 0o007,
        "logger_class": "gunicorn.glogging.Logger",
    }

    if opts is not None:
        options.update(opts)

    return GunicornApp(app, options)
