from certifi import where
import requests, web, json

urls = (
    '/history', 'history_index',
    '/settings', 'settings_index',
    '/analysis', 'analysis_index'
)

db = web.database( 
    dbn='postgres', 
    host='127.0.0.1', 
    port=5432,
    user='postgres',
    db='postgres',
    pw='hgg'
)

def to_json(obj):
    return json.loads(json.dumps(obj))

def get_url():
    return web.ctx.fullpath

def to_list(obj):
    res = []
    for data in obj:
        res.append(to_json(data.value))
    return res

class history_index:
    def POST(self):
        print(web.data().decode())
        data = json.loads(web.data())
        # 往数据库插入一条垃圾放置数据
        db.insert('history_tb', key=data['time'], value=json.dumps(data))
        # 更新垃圾桶当前的容量
        id = data['position']
        res = db.select('settings_tb', what="value", where={'settings_tb.key': id})
        res = to_json(res[0].value)
        res['data']['curCapacity'] += 1
        res['data']['capacityRate']
        db.update('settings_tb', where={'settings_tb.key': id}, value=json.dumps(res))
    
    def GET(self):
        # 返回所有垃圾放置数据
        res = db.select('history_tb', what="value")
        res = to_list(res)
        web.header("Access-Control-Allow-Origin", "*")
        web.header("Content-Type", "application/json")
        return json.dumps(res)

class settings_index:
    
    def GET(self):
        # 查询某一个/所有垃圾站点的数据
        data = web.data().decode()
        if data == "":
            res = db.select('settings_tb', what="value")
            res = to_list(res)
        else :
            res = db.select('settings_tb', what="value", where={"key": data})
            res = to_list(res)[0]
        web.header("Content-Type", "application/json")
        web.header("Access-Control-Allow-Origin", "*")
        return json.dumps(res)

    def POST(self):
        # 修改数据库中jetson的设置
        data = json.loads(web.data())
        id = data['data']['id']
        res = db.select('settings_tb', what="value")
        res = to_json(res[0].value)
        data['data']['curCapacity'] = res['data']['curCapacity']
        db.update('settings_tb', where={'settings_tb.key': id}, value=json.dumps(data))
        header = { "Access-Control-Allow-Origin": "*", "Content-Type": "application/json", }
        try:
            requests.post(data['data']['url'], data=json.dumps(data), headers=header, timeout=6)
        except Exception as e:
            print('Post error: %s'%(str(e)))


    def PUT(self):
        data = json.loads(web.data())
        # 添加jetson的设置
        db.insert('settings_tb', key=data['data']['id'], value=json.dumps(data))

    def OPTIONS(self):
        pass

class analysis_index:
    def GET(self):
        data = web.input()
        res = []
        if data['type'] == 'pie':
            res = db.select(
                'history_tb', 
                what="history_tb.value::json #>> '{type}' as name, count(*) as value", 
                group="history_tb.value::json #>> '{type}'"
            )
            res = list(res)
        if data['type'] == 'bar':
            res = db.select(
                'history_tb', 
                what="split_part(history_tb.value::json #>> '{time}', ' ', 1) as day," 
                     "sum(case history_tb.value::json #>> '{type}' when 'food' then 1 else 0 end) as food, "
                     "sum(case history_tb.value::json #>> '{type}' when 'residual' then 1 else 0 end) as residual, "
                     "sum(case history_tb.value::json #>> '{type}' when 'hazardous' then 1 else 0 end) as hazardous, "
                     "sum(case history_tb.value::json #>> '{type}' when 'recyclable' then 1 else 0 end) as recyclable",
                group="day"
            )
            res = list(res)
        web.header("Access-Control-Allow-Origin", "*")
        web.header("Content-Type", "application/json")
        return json.dumps(res)    

if __name__ == "__main__":
    app = web.application(urls, globals())
    app.run()

