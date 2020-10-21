from abc import ABC
from typing import Optional, Awaitable

import tornado.ioloop
import tornado.web
from tornado.web import url
import handler
import json
import urllib.parse
import traceback


class ErrorResponse:
    code = None
    message = None

    def __init__(self, code, message):
        self.code = code
        self.message = message


class BaseHandler(tornado.web.RequestHandler):
    def data_received(self, chunk: bytes) -> Optional[Awaitable[None]]:
        raise

    db = None
    json_args = None

    STATUS_CODE_OK = 200
    STATUS_CODE_ROUTE_MISSING = 404
    STATUS_CODE_SYS = 500

    ERROR_OK = ErrorResponse(0, "ok")
    ERROR_ROUTE_MISSING = ErrorResponse(400, "route missing for requested url, maybe mistyping or removed ")
    ERROR_SYS = ErrorResponse(500, "unknown server error")

    def initialize(self, db=None):
        self.db = db

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


def make_app():
    db = {"name": "db1"}

    return tornado.web.Application(
        [
            url(r"/story/([%0-9a-zA-Z]+)", handler.StoryHandler, dict(db=db), name="story")
        ]
        , debug=True
        , default_handler_class=DefaultHandler
    )


if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
