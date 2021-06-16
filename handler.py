import datetime
from app import BaseHandler
from chatdemo import database
import aiomysql.cursors
import aiopg.cursor


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
        async with self.mysql.acquire() as conn:
            sql = self.json_args["sql"]
            cur = await conn.connection.cursor(aiomysql.cursors.DictCursor)
            await cur.execute(sql)
            self.write_json(data=await cur.fetchall())

    async def query2(self):
        async with self.postgres.acquire() as conn:
            sql = self.json_args["sql"]
            async with conn.connection.cursor(aiopg.cursor.Cursor) as cur:
                await cur.execute(sql)
                self.write_json(data=await cur.fetchall())

    async def query3(self):
        self.write_json(data={"a":1}, status_code=401)
