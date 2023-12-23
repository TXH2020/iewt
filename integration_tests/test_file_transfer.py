import aiohttp
import asyncio
import json
import ast
import re
import datetime
import os
from websocket import create_connection
import unittest
import select
ws=None

def send(x):
    global ws
    ws.send(x)

def recieve():
    global ws
    return ws.recv()

async def websocket_connection():
    global ws
    async with aiohttp.ClientSession() as session:
        creds=('osboxes','osboxes','osboxes.org')
        url='http://localhost:8888?hostname=%s&username=%s&password=%s'%creds
        async with session.post(url) as response:
            dictionary = await response.json()
            ws = create_connection("ws://localhost:8888/ws?id="+dictionary.get('id'))
            while(True):
                r,_,_=select.select([ws],[],[])
                if r:
                    break
            print("Connection dict:", dictionary)
asyncio.run(websocket_connection())

class TestFileTransfer(unittest.TestCase):
    def test_file_transfer(self):
        path=input("Enter a filepath")
        if(os.path.isfile(path)):
            x={"file_transfer":path}
            json_data = ast.literal_eval(json.dumps(x))
            send(json.dumps(json_data))
            start_time=datetime.datetime.now()
            while(True):
                r,_,_=select.select([ws],[],[])
                end_time=datetime.datetime.now()
                if((end_time-start_time).total_seconds()>=5):
                    self.assertEqual(False, True, "Unsuccessful")
                    break
                if(r):
                    data=recieve()
                    try:
                        x1=re.search(r"Successful!",data)
                        if(x1):
                            self.assertEqual(True, True, "Unsuccessful")
                            break
                    except:
                        pass
        else:
            self.assertEqual(False, True, "Unsuccessful")
                
if __name__ == '__main__':
    unittest.main()


