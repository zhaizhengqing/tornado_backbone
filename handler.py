import datetime
from app import BaseHandler
from chatdemo import database


class StoryHandler(BaseHandler):

    async def get(self):
        async with self.db.acquire() as conn:
            cur = await conn.connection.cursor()
            await cur.execute("desc tbl")
            print(await cur.fetchall())
            await conn.execute(database.tbl.insert().values(val='abc'))
            await conn.execute(database.tbl.insert().values(val='xyz'))

        self.write("this is method %s, %s, %s" % ('1', '1', datetime.datetime.now().strftime("%s")))


class DbHandler(BaseHandler):
    async def query(self):
        async with self.db.acquire() as conn:
            sql = self.json_args["sql"]
            cur = await conn.connection.cursor()
            await cur.execute(sql)
            self.write_json(data=await cur.fetchall())
