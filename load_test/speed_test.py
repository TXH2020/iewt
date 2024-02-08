import aiohttp
import asyncio
from websocket import create_connection
import select
from timeit import default_timer as timer
import time
import json
import ast
import numpy as np
import re

ws=None
def format(string):
    x={'command':string}
    json_data = ast.literal_eval(json.dumps(x))
    return json.dumps(json_data)

async def websocket_connection():
    global ws
    async with aiohttp.ClientSession() as session:
        h,u,p=('osboxes','osboxes','osboxes.org')
        url='http://localhost:8888?hostname={0}&username={1}&password={2}'.format(h,u,p)
        async with session.post(url) as response:
            dictionary = await response.json()
            ws = create_connection("ws://localhost:8888/ws?id="+dictionary.get('id'))
            while(True):
                r,_,_=select.select([ws],[],[])
                if r:
                    break

asyncio.run(websocket_connection())    

avg=[]
savg=[]
for i in range(100):
    start=timer()
    ws.send(format("sleep 0.1 && echo tejas"+"#;echo #"+"id"+"#:Status=$?time-$((`date '+%s'`))_\r#"+"ws_url"))
    send_stop=timer()
    while(True):
        r,_,_=select.select([ws],[],[])
        if(r):
            data=ws.recv()
            end=timer()
            try:
                x=json.loads(data)
                savg.append(send_stop-start)
                avg.append(end-start)
                break
            except:
                pass

print("Interactive execution average time:",np.mean(avg))
print("Median time:",np.median(avg))
print("Average message transmission time:",np.mean(savg))

avg=[]
savg=[]
for i in range(100):
    start=timer()
    ws.send(format("sleep 0.1 && echo tejas$?\r"))
    send_stop=timer()
    while(True):
        r,_,_=select.select([ws],[],[])
        if(r):
            data=ws.recv()
            end=timer()
            try:
                x1=re.search("tejas0",data.decode())
                if(x1):
                    savg.append(send_stop-start)
                    avg.append(end-start)
                    break
            except:
                pass

print("Direct execution average time:",np.mean(avg))
print("Median time:",np.median(avg))
print("Average message transmission time:",np.mean(savg))
ws.close()

asyncio.run(websocket_connection())  
rate=0
steps=10000000
while(True):
    string='A'*steps+'\r'
    try:
        start=timer()
        ws.send(format(string))
        end=timer()
        print(end-start)
        if(end-start>=1.0):
            break
    except BrokenPipeError:
        print("Maximum Limit reached")
        break
    except:
        steps+=1
        print("Socket timeout on server")
        
print(steps," kB/s is supported")


    


