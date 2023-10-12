import logging
try:
    import secrets
except ImportError:
    secrets = None
import tornado.websocket
from uuid import uuid4
from tornado.ioloop import IOLoop
from tornado.iostream import _ERRNO_CONNRESET
from tornado.util import errno_from_exception
#additional libraries
import requests
from datetime import datetime
import re
import os

BUF_SIZE = 32 * 1024
clients = {}  # {ip: {id: worker}}

#For logging terminal sessions
current_dir=os.getcwd()
if(os.path.exists(os.path.join(current_dir,'logs'))==False):
   os.mkdir('logs')
log_directory=os.path.join(current_dir,'logs')

def clear_worker(worker, clients):
    ip = worker.src_addr[0]
    workers = clients.get(ip)
    assert worker.id in workers
    workers.pop(worker.id)

    if not workers:
        clients.pop(ip)
        if not clients:
            clients.clear()


def recycle_worker(worker):
    if worker.handler:
        return
    logging.warning('Recycling worker {}'.format(worker.id))
    worker.close(reason='worker recycled')


class Worker(object):
    def __init__(self, loop, ssh, chan, dst_addr):
        self.loop = loop
        self.ssh = ssh
        self.chan = chan
        self.dst_addr = dst_addr
        self.fd = chan.fileno()
        self.id = self.gen_id()
        self.data_to_dst = []
        self.handler = None
        self.mode = IOLoop.READ
        self.closed = False
        #the variables defined below are for various purposes. To add one, simpy write self.<variable_name>
        self.input_command=None
        self.command_id=None
        self.entry_timestamp=None
        self.conn=None
        self.conn_status=0
        self.search_id=None
        self.search_bit=0
        self.search_command=None
        
        try:
            self.conn=requests.Session()
            self.conn.get('http://localhost:5000/test')
            self.conn_status=1
        except Exception as e:
            logging.info(e)

    def __call__(self, fd, events):
        if events & IOLoop.READ:
            self.on_read()
        if events & IOLoop.WRITE:
            self.on_write()
        if events & IOLoop.ERROR:
            self.close(reason='error event occurred')        
            
    #to extract the command execution status and time taken to execute the comand
    def get_time_status(self,text):
        command_execution_status=''
        execution_time=''
        t=text.decode()
        cst=re.search('Command_Execution_Status=[0-9]{1,3}',t)
        search_text_match=None
        if(self.search_id):
            try:
                search_text_match=re.search(self.search_id+':'+'Command_Execution_Status=[0-9]{1,3}',t)
                if(search_text_match):
                    self.search_bit=1
            except:
                pass
        if((cst and self.input_command) or self.search_bit==1):
            exit_time=datetime.now()
            if(self.search_bit==1):
                cst=search_text_match
            execution_time=execution_time+str(round((exit_time-self.entry_timestamp).total_seconds(),2))+"s"
            equal_pos=re.search("=",t[cst.start():cst.end()]).start()
            command_execution_status+=t[cst.start()+equal_pos+1:cst.end()]
            logging.info("Command status and time recieved")
        return command_execution_status,execution_time
            
    def send_command(self,command_execution_status,execution_time):
           try:
                data={"session_id":self.id,"command_id":self.command_id,"command":self.input_command,"command_Execution_Status"
                      :command_execution_status,"execution_Time":execution_time,"timestamp":str(self.entry_timestamp)}
                self.conn.post("http://localhost:5000/command",json=data)
                logging.info("record sent successfully")
           except Exception as e:
               logging.info(e)
    
    @classmethod
    def gen_id(cls):
        return secrets.token_urlsafe(nbytes=32) if secrets else uuid4().hex

    def set_handler(self, handler):
        if not self.handler:
            self.handler = handler

    def update_handler(self, mode):
        if self.mode != mode:
            self.loop.update_handler(self.fd, mode)
            self.mode = mode
        if mode == IOLoop.WRITE:
            self.loop.call_later(0.1, self, self.fd, IOLoop.WRITE)
            
    def on_read(self):
        logging.debug('worker {} on read'.format(self.id))
        try:
            data = self.chan.recv(BUF_SIZE)
            #for logging terminal session into a log file. It is stored where we invoke the server
            with open(os.path.join(log_directory,self.id+'.log'),'ab') as f:
                f.write(data)
            #obtain command execution status and time
            command_execution_status,execution_time=self.get_time_status(data)
        except (OSError, IOError) as e:
            logging.error(e)
            if self.chan.closed or errno_from_exception(e) in _ERRNO_CONNRESET:
                self.close(reason='chan error on reading')
        else:
            logging.debug('{!r} from {}:{}'.format(data, *self.dst_addr))
            if not data:
                self.close(reason='chan closed')
                return

            logging.debug('{!r} to {}:{}'.format(data, *self.handler.src_addr))
            try:
                #if we have obtained status and time for an inserted command.
                if(command_execution_status and execution_time and (self.input_command or self.search_bit==1)):
                    result_string=';!@#{"Command_Execution_Status":"'+command_execution_status+'","Execution_Time":"'+execution_time+'"}#@!;'
                    res = bytes(result_string, 'utf-8')
                    #To send status and time back to client
                    self.handler.write_message(res, binary=True)
                    #If it is not search mode only then log and send to db service
                    if(self.search_bit==1):
                        self.input_command=self.search_command
                        self.command_id=self.search_id
                        self.search_bit=0
                        self.search_id=None
                    logging.info("Command ID:"+self.command_id+",Command:"+self.input_command+",Command Status:"+
                                 command_execution_status+",Execution time:"+execution_time+
                                 ",Timestamp:"+str(self.entry_timestamp))
                    #Send command to database service.
                    if(self.conn_status==1):
                        self.send_command(command_execution_status,execution_time)
                    #To clear inserted command to enable entry of next
                    self.input_command=None
                    self.entry_timestamp=None
                    self.command_id=None
                self.handler.write_message(data, binary=True)
            except tornado.websocket.WebSocketClosedError:
                self.close(reason='websocket closed')

    def on_write(self):
        logging.debug('worker {} on write'.format(self.id))
        if not self.data_to_dst:
            return

        data = ''.join(self.data_to_dst)
        logging.debug('{!r} to {}:{}'.format(data, *self.dst_addr))

        try:
            sent = self.chan.send(data)
        except (OSError, IOError) as e:
            logging.error(e)
            if self.chan.closed or errno_from_exception(e) in _ERRNO_CONNRESET:
                self.close(reason='chan error on writing')
            else:
                self.update_handler(IOLoop.WRITE)
        else:
            self.data_to_dst = []
            data = data[sent:]
            if data:
                self.data_to_dst.append(data)
                self.update_handler(IOLoop.WRITE)
            else:
                self.update_handler(IOLoop.READ)
    
        
    def close(self, reason=None):
        if self.closed:
            return
        self.closed = True

        logging.info(
            'Closing worker {} with reason: {}'.format(self.id, reason)
        )
        if self.handler:
            self.loop.remove_handler(self.fd)
            self.handler.close(reason=reason)
        self.chan.close()
        self.ssh.close()
        self.conn.close()
        logging.info('Connection to {}:{} lost'.format(*self.dst_addr))

        clear_worker(self, clients)
        logging.debug(clients)

        
