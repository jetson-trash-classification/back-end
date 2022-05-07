from asyncio.windows_events import NULL
import requests
import web
import json

urls = (
    '/history(.*)', 'history_index',
    '/settings(.*)', 'settings_index'
)

db = web.database( 
    dbn='postgres', 
    host='127.0.0.1', 
    port=5432,
    user='postgres',
    db='postgres',
    pw='hgg'
)

jetson_url = 'http://192.168.137.10:3000'

def to_json(obj):
    return json.loads(json.dumps(obj))

def get_url():
    return web.ctx.fullpath

class history_index:
    def POST(self, data):
        # 往数据库插入一条垃圾放置数据
        db.insert('history_tb', key=data.time, value=json.dumps(data))
    
    def GET(self, data):
        # 返回所有垃圾放置数据
        data_list = db.select('history_tb', what="value")
        res = []
        for data in data_list:
            res.append(to_json(data))
        web.header("Access-Control-Allow-Origin", "*")
        web.header("Content-Type", "application/json")
        return json.dumps(res)

class settings_index:
    
    def GET(self, id):
        # 查询数据库，返回数据
        if id is NULL:
            res = db.select('settings_tb', where={'settings_tb.key': id}, what="value")
            res = list(res)
        else:
            res = db.select('settings_tb', where={'settings_tb.key': id}, what="value")
            res = to_json(res[0])
        web.header("Access-Control-Allow-Origin", "*")
        return res

    def POST(self, data):
        # 修改jetson数据库
        id = data.id
        db.update('settings_tb', where={'settings_tb.key': id}, what="value")

        # 往jetson发送一条数据
        requests.post(url=jetson_url, data=data)


if __name__ == "__main__":
    app = web.application(urls, globals())
    app.run()

