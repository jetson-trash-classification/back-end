import requests, web, json

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

def to_list(obj):
    res = []
    for data in obj:
        res.append(to_json(data))
    return res

class history_index:
    def POST(self, data):
        # 往数据库插入一条垃圾放置数据
        db.insert('history_tb', key=data.time, value=json.dumps(data))
        # 更新垃圾桶当前的容量
        id = data.position
        res = db.select('settings_tb', what="value", where={'settings_tb.key': id})
        res = to_json(res[0])
        res.curCapacity += 1
        db.update('settings_tb', where={'settings_tb.key': id}, value=json.dumps(res))
    
    def GET(self, data):
        # 返回所有垃圾放置数据
        res = db.select('history_tb', what="value")
        res = to_list(res)
        web.header("Access-Control-Allow-Origin", "*")
        web.header("Content-Type", "application/json")
        return json.dumps(res)

class settings_index:
    
    def GET(self, id):
        # 查询某一个/所有垃圾站点的数据
        if id is None:
            res = db.select('settings_tb', what="value")
            res = to_list(res)
        else:
            res = db.select('settings_tb', where={'settings_tb.key': id}, what="value")
            res = to_json(res[0])
        web.header("Access-Control-Allow-Origin", "*")
        return res

    def POST(self, data):
        # 修改数据库中jetson的设置
        id = data.id
        res = db.select('settings_tb', what="value")
        res = to_json(res[0])
        data.curCapacity = res.curCapacity
        db.update('settings_tb', where={'settings_tb.key': id}, value=json.dumps(data))

        # 修改jetson中的设置
        requests.post(url=jetson_url, data=data)
    
    def PUT(self, data):
        # 添加jetson的设置
        db.insert('settings_tb', key=id, value=json.dumps(data))


if __name__ == "__main__":
    app = web.application(urls, globals())
    app.run()

