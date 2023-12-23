import aiohttp
import asyncio
from websocket import create_connection
import select
import time
import json
import ast
wsconns=[]

def format(string):
    x={'command':string}
    json_data = ast.literal_eval(json.dumps(x))
    return json.dumps(json_data)

async def websocket_connection():
    global wsconns
    async with aiohttp.ClientSession() as session:
        h,u,p=('20.83.180.145','iewt','Juo987Hj*67jkiuop')
        url='http://localhost:8888/index?hostname={0}&username={1}&password={2}'.format(h,u,p)
        async with session.post(url) as response:
            dictionary = await response.json()
            ws = create_connection("ws://localhost:8888/index/ws?id="+dictionary.get('id'))
            while(True):
                r,_,_=select.select([ws],[],[])
                if r:
                    break
            wsconns.append(ws)
            print("Connection dict:", dictionary)


n=int(input("Enter no. of connections:"))
success_count=0
for i in range(n):
   asyncio.run(websocket_connection())
   success_count+=1
print("No. of successful connections=",success_count)
time.sleep(2)
for i in range(success_count):
    wsconns[i].send(format('top\r'))
print("Command top sent to all connections")
time.sleep(10)
for i in range(success_count):
    wsconns[i].close()
