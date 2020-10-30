import datetime
from app import BaseHandler


class StoryHandler(BaseHandler):

    async def get(self):
        self.write("this is method %s, %s, %s" % ('1', self.db["name"], datetime.datetime.now().strftime("%s")))
