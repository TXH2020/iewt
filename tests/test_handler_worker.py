import aiohttp
import asyncio
import json
import ast
import re
import datetime
import select
import os
from websocket import create_connection
import unittest
import sqlite3
ws=None

def send(x):
    global ws
    ws.send(x)

def recieve():
    global ws
    return ws.recv()

def format(string):
    x={'command':string}
    json_data = ast.literal_eval(json.dumps(x))
    return json.dumps(json_data)

async def websocket_connection():
    global ws
    async with aiohttp.ClientSession() as session:
        creds=('osboxes','osboxes','osboxes.org')
        url='http://localhost:8888/index?hostname=%s&username=%s&password=%s'%creds
        async with session.post(url) as response:
            dictionary = await response.json()
            ws = create_connection("ws://localhost:8888/index/ws?id="+dictionary.get('id'))
            while(True):
                r,_,_=select.select([ws],[],[])
                if r:
                    break
            print("Connection dict:", dictionary)
            x={"test":"1"}
            json_data = ast.literal_eval(json.dumps(x))
            send(json.dumps(json_data))
asyncio.run(websocket_connection())

class TestHandlerWorker(unittest.TestCase):
    def test_command_execution_status_correct(self):
        send(format("hostname"+"#;echo #"+"id"+"#:Status=$?time-$((`date '+%s'`))_\r#"+"ws_url"))
        start_time=datetime.datetime.now()
        while(True):
            r,_,_=select.select([ws],[],[])
            end_time=datetime.datetime.now()
            if((end_time-start_time).total_seconds()>=5):
                self.assertEqual(False, True, "Unsuccessful")
                break
            if(r):
                try:
                    x=json.loads(recieve())
                    if(x['status']=='0'):
                        self.assertEqual(True, True, "Unsuccessful")
                    else:
                        self.assertEqual(False, True, "Unsuccessful")
                    break
                except:
                    pass
    
    def test_command_execution_status_wrong(self):
        send(format("hostname2"+"#;echo #"+"id"+"#:Status=$?time-$((`date '+%s'`))_\r#"+"ws_url"))
        start_time=datetime.datetime.now()
        while(True):
            r,_,_=select.select([ws],[],[])
            end_time=datetime.datetime.now()
            if((end_time-start_time).total_seconds()>=5):
                self.assertEqual(False, True, "Unsuccessful")
                break
            if(r):
                try:
                    x=json.loads(recieve())
                    if(x['status']!='0'):
                        self.assertEqual(True, True, "Unsuccessful")
                    else:
                        self.assertEqual(False, True, "Unsuccessful")
                    break
                except:
                    pass
    
    def test_command_execution_only(self):
        send(format("hostname\r"))
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
            
    def test_wrong1(self):
        send(format("hostname"+"#;echo1 #"+"id"+"#:Status=$?time-$((`date '+%s'`))_\r#"+""))
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
                    x1=re.search(r"Unsuccessful!",data)
                    if(x1):
                        self.assertEqual(True, True, "Unsuccessful")
                        break
                except:
                    pass
    
    def test_wrong2(self):
        os.chdir('/home/osboxes/Desktop/final_test')
        con=sqlite3.connect("entry_time_backup.db")
        cur=con.cursor()
        cur.execute("insert into entry_time_table values (?,?)",("ws_urltest","12345678.1234"))
        con.commit()
        send(format("hostname"+"#id"+"#ws_urltest"))
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
                    x1=re.search(r"Unsuccessful!",data)
                    if(x1):
                       self.assertEqual(True, True, "Unsuccessful")
                       cur.execute("delete from entry_time_table where session_id=?",("ws_urltest",))
                       con.commit()
                       con.close()
                       break
                except:
                    pass
    
if __name__ == '__main__':
    unittest.main()

