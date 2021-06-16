from abc import ABC
from typing import Optional, Awaitable
import tornado.options
import tornado.ioloop
import tornado.web
import tornado.locks
from tornado.web import url
import handler
import json
import urllib.parse
import traceback
import pathlib
import os
import aiomysql.sa
import aiopg.sa
import asyncio

app_path = pathlib.Path(__file__).parent.absolute()
static_path = os.path.join(app_path, "static")


class ErrorResponse:
    code = None
    message = None

    def __init__(self, code, message):
        self.code = code
        self.message = message


class BaseHandler(tornado.web.RequestHandler):
    def data_received(self, chunk: bytes) -> Optional[Awaitable[None]]:
        raise

    mysql = None
    postgres = None
    json_args = None

    STATUS_CODE_OK = 200
    STATUS_CODE_ROUTE_MISSING = 404
    STATUS_CODE_SYS = 500

    ERROR_OK = ErrorResponse(0, "ok")
    ERROR_ROUTE_MISSING = ErrorResponse(400, "route missing for requested url, maybe mistyping or removed ")
    ERROR_SYS = ErrorResponse(500, "unknown server error")

    def initialize(self, mysql=None, postgres=None):
        self.mysql = mysql
        self.postgres = postgres

    async def prepare(self):
        if self.is_json_request():
            self.json_args = json.loads(self.request.body)
        await self.dispatch()
        self.finish()

    async def dispatch(self):
        # url parse and route to class method
        parse_result = urllib.parse.urlparse(self.request.uri)
        path_parts = parse_result.path.split("/")
        path_class = path_parts[1]
        path_method = path_parts[2]
        if not hasattr(self, path_method):
            raise tornado.web.HTTPError(self.STATUS_CODE_ROUTE_MISSING, "method not found in class: %s" % (path_class,))
        method = getattr(self, path_method)
        await method()

    def is_json_request(self):
        if self.request.headers.get("Content-Type", "").startswith("application/json"):
            return True
        else:
            return False

    def on_finish(self):
        pass

    def on_connection_close(self):
        print("on_connection_close")

    def write_error(self, status_code, **kwargs):
        exc_type, exc_val, tb = kwargs["exc_info"]
        traceback_info = traceback.format_exception(exc_type, exc_val, tb)
        error_response = self.ERROR_SYS
        status_code = self.STATUS_CODE_SYS
        if exc_type is tornado.web.HTTPError:
            error_response = self.ERROR_ROUTE_MISSING
            status_code = self.STATUS_CODE_ROUTE_MISSING
        if self.is_json_request():
            debug_info = {"except": str(exc_val), "traceback": traceback_info}
            self.write_json(code=error_response.code, message=error_response.message, debug=debug_info,
                            status_code=status_code)
        else:
            self.write_html("%s\n%s\n%s" % (error_response.message, exc_val, "".join(traceback_info)), status_code)

    def write_json(self, data=None, code=ERROR_OK.code, message=ERROR_OK.message, debug=None,
                   status_code=STATUS_CODE_OK):
        self.set_status(status_code)
        result = {"code": code, "message": message, "data": data, "debug": debug}
        self.write(result)

    def write_html(self, html, status_code=STATUS_CODE_OK):
        self.set_status(status_code)
        self.write(html)

    def set_default_headers(self):
        pass


class DefaultHandler(BaseHandler):
    async def prepare(self):
        if self.is_json_request():
            self.write_json(code=self.ERROR_ROUTE_MISSING.code, message=self.ERROR_ROUTE_MISSING.message,
                            status_code=self.STATUS_CODE_ROUTE_MISSING)
        else:
            self.write_html(html=self.ERROR_ROUTE_MISSING.message, status_code=self.STATUS_CODE_ROUTE_MISSING)
        self.finish()


def make_app(mysql, postgres):
    return tornado.web.Application(
        [
            url(r"/static/(.*)", tornado.web.StaticFileHandler, dict(path=static_path)),
            url(r"/story/([%0-9a-zA-Z]+)", handler.StoryHandler, dict(mysql=mysql, postgres=postgres), name="story"),
            url(r"/db/([%0-9a-zA-Z]+)", handler.DbHandler, dict(mysql=mysql, postgres=postgres), name="db")
        ]
        , debug=True
        , default_handler_class=DefaultHandler
    )


async def main():
    loop = tornado.ioloop.IOLoop.current()
    tornado.options.parse_command_line()
    async with aiomysql.sa.create_engine(
            user="zhaizhengqing", db="zhaizhengqing", port=3306, host="192.168.56.1", password="123654",
            connect_timeout=3000, loop=loop.asyncio_loop
    ) as mysql:
        async with aiopg.sa.create_engine(
                user='zhaizhengqing', database='zhaizhengqing', host='192.168.56.1',
                password='123654', connect_timeout=3000) as postgres:
            app = make_app(mysql=mysql, postgres=postgres)
            app.listen(8888)
            shutdown_event = tornado.locks.Event()
            await shutdown_event.wait()


if __name__ == "__main__":
    tornado.ioloop.IOLoop.current().run_sync(main)
