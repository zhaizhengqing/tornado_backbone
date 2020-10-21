from abc import ABC
from typing import Optional, Awaitable

import tornado.ioloop
import tornado.web
from tornado.web import url
from handler import *
import traceback


class BaseHandler(tornado.web.RequestHandler):
    def data_received(self, chunk: bytes) -> Optional[Awaitable[None]]:
        raise

    db = None
    json_args = None

    STATUS_CODE_OK = 200
    STATUS_CODE_SYS = 500

    ERROR_CODE_OK = 0
    ERROR_CODE_SYS = 500

    def initialize(self, db):
        print("initialize")
        self.db = db

    def prepare(self):
        print("prepare")
        if self.is_json_request():
            self.json_args = json.loads(self.request.body)

    def is_json_request(self):
        if self.request.headers.get("Content-Type", "").startswith("application/json"):
            return True
        else:
            return False

    def on_finish(self):
        print("on_finished")

    def on_connection_close(self):
        print("on_connection_close")

    def write_error(self, status_code, **kwargs):
        exc_type, exc_val, tb = kwargs["exc_info"]
        traceback_info = traceback.format_exception(exc_type, exc_val, tb)
        if self.is_json_request():
            debug_info = {"traceback": traceback_info}
            self.write_json(code=self.ERROR_CODE_SYS, message=str(exc_val), debug=debug_info,
                            status_code=self.STATUS_CODE_SYS)
        else:
            self.write_html("%s\n%s" % (exc_val, "".join(traceback_info)), self.STATUS_CODE_SYS)

    def write_json(self, data=None, code=ERROR_CODE_OK, message="success", debug=None, status_code=STATUS_CODE_OK):
        self.set_status(status_code)
        result = {"code": code, "message": message, "data": data, "debug": debug}
        self.write(result)

    def write_html(self, html, status_code=STATUS_CODE_OK):
        self.set_status(status_code)
        self.write(html)

    def set_default_headers(self):
        print("set_default_headers")


def make_app():
    db = {"name": "db1"}

    return tornado.web.Application(
        [
            url(r"/", MainHandler),
            url(r"/story/([0-9]+)", StoryHandler, dict(db=db), name="story")
        ]
        , debug=True
    )


if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
