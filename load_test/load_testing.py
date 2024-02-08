import aiohttp
import asyncio
from websocket import create_connection
import select
from timeit import default_timer as timer
import time
import json
import ast
import psutil
wsconns=[]

def format(string):
    x={'command':string}
    json_data = ast.literal_eval(json.dumps(x))
    return json.dumps(json_data)

async def websocket_connection():
    global wsconns
    async with aiohttp.ClientSession() as session:
        h,u,p=('osboxes','osboxes','osboxes.org')
        url='http://localhost:8888?hostname={0}&username={1}&password={2}'.format(h,u,p)
        async with session.post(url) as response:
            dictionary = await response.json()
            ws = create_connection("ws://localhost:8888/ws?id="+dictionary.get('id'))
            wsconns.append(ws)



PROCNAME = "iewt"
pid=None
for proc in psutil.process_iter():
    if proc.name() == PROCNAME:
        pid=proc.pid
iewt_proc=psutil.Process(pid)


n=int(input("Enter no. of connections:"))
success_count=0
for i in range(n):
    try:
        start = timer()
        asyncio.run(websocket_connection())
        end = timer()
        success_count+=1
        print("Time=",(end-start),"s","\t",success_count)
        if(i%100==0):
            print("Memory%=",iewt_proc.memory_percent(),"CPU%=",(iewt_proc.cpu_percent() / psutil.cpu_count()))
    except Exception as e:
        print(e)

print("No. of successful connections=",success_count)
for i in range(success_count):
    wsconns[i].close()
