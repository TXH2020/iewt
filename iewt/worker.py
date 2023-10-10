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
import mysql.connector as my
import re
BUF_SIZE = 32 * 1024
clients = {}  # {ip: {id: worker}}

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
        self.coflag=0
        self.timeflag1=0
        self.timeflag2=0
        self.temp=0
        self.temp_time_storage=""
        self.input_command=[]
        self.command_ids=[]
        self.timestamp=[]
        self.session_close_flag=1
        self.cnx=None
        self.mysqlcon_status=0
        
        try:
            self.cnx=my.connect(user="root",host="localhost",password="")
            self.mysqlcon_status=1
        except my.Error as e:
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
        execution_time=''
        command_execution_status=''
        t=text.decode()
        if(self.temp==1):
            self.temp=self.temp+1
        #co,ro,so,cst are match objects
        #r,c are indices for 'real' and 'Command_Execution_Status:' respectively
        co=re.search("COMMAND_OUTPUT!@#",t)
        if(co):
            self.coflag=1
        if(self.coflag==1):
            ro=re.search('real',t)
            r=-1
            if(ro):
                logging.info("Command time recieved")
                self.temp=1
                self.timeflag1=1
                r=ro.start()
            try:
                if(self.timeflag1==1):
                    tstart,tend=-1,-1
                    if(self.temp==1):
                        tstart=re.search('\d+\.\d+',t[r:]).start()
                        tend=re.search('s',t[r:]).start()
                        execution_time=execution_time+t[r:][tstart:tend+1]
                    else:
                        tstart=re.search('\d+\.\d+',t).start()
                        tend=re.search('s',t).start()
                        execution_time=execution_time+t[tstart:tend+1]
                    self.timeflag1=0
                    self.timeflag2=1
                    self.temp_time_storage=execution_time
            except:
                    pass
            c=-1
            if(self.timeflag2==1):
                try:
                    if(self.temp==1):
                        c=re.search('Command_Execution_Status:',t[r:]).start()
                        cstring=t[r:][c:].split(':')[1].rstrip('\r')
                        cst=re.search('[0-9]{1,3}',cstring)
                        command_execution_status=command_execution_status+cstring[cst.start():cst.end()]
                    else:
                        c=re.search('Command_Execution_Status:',t).start()
                        cstring=t[c:].split(':')[1].rstrip('\r')
                        cst=re.search('[0-9]{1,3}',cstring)
                        command_execution_status=command_execution_status+cstring[cst.start():cst.end()]
                    self.temp=0
                    self.coflag=0
                    self.timeflag2=0
                    execution_time=self.temp_time_storage
                except:
                    pass
        return command_execution_status,execution_time
    
    #To pass command id to the client
    def push_command_id(self):
       if(len(self.input_command)!=0):
        try:
            res=bytes("!@#Command_ID:"+self.command_ids[0], 'utf-8')
            self.handler.write_message(res, binary=True)
        except:
            self.close(reason='websocket closed')
            
    def insert_command(self,command_execution_status,execution_time):
           cr=self.cnx.cursor(buffered=True)
           cr.execute("use command_database")
           add_command = ("INSERT INTO command_table"
                "(Command_ID,Command,Command_Execution_Status,Execution_Time,Timestamp)"
                 "VALUES (%s, %s, %s, %s,%s)")
           command=(self.command_ids[0],self.input_command[0],command_execution_status,execution_time,self.timestamp[0])
           try:
                cr.execute(add_command,command)
                logging.info("record was successfully inserted")
           except Exception as e:
                logging.info(e)
           try:
               self.cnx.commit()
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
            with open('log.txt','ab') as f:
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
                if(command_execution_status and execution_time and len(self.input_command)!=0):
                    if(self.session_close_flag==0):
                        self.session_close_flag=1
                        self.insert_command(command_execution_status,execution_time)
                        self.mysqlcon_status=0
                        self.cnx.close()
                        self.clean_up("client disconnected")
                    logging.info("Command:"+self.input_command[0]+",Command_ID:"+self.command_ids[0]+",Command Status:"+
                                 command_execution_status+",Execution time:"+execution_time+
                                 ",Timestamp:"+str(self.timestamp[0]))
                    #Insert command information into database
                    if(self.mysqlcon_status==1 and len(self.input_command)!=0):
                        self.insert_command(command_execution_status,execution_time)
                    test_string=';!@#{"Command_Execution_Status":"'+command_execution_status+'","Execution_Time":"'+execution_time+'"}#@!;'
                    res = bytes(test_string, 'utf-8')
                    #To send status and time back to client
                    self.handler.write_message(res, binary=True)
                    #To clear inserted command to enable entry of next
                    self.input_command.pop(0)
                    self.command_ids.pop(0)
                    self.timestamp.pop(0)
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
    
    #perform cleanup operations
    def clean_up(self,reason):
        self.closed = True
        if self.handler:
            self.loop.remove_handler(self.fd)
            self.handler.close(reason=reason)
        self.chan.close()
        self.ssh.close()
        clear_worker(self, clients)
        logging.debug(clients)
        
    def close(self, reason=None):
        if self.closed:
            return
        
        logging.info(
            'Closing worker {} with reason: {}'.format(self.id, reason)
        )
        #Suppose client has a reload event which causes disconnection but a command was still executing; we havent recieved
        #the status and time for that command. Hence prevent that session from closing till the command executes successfully
        #However, the commands are assumed to be those which do ask for parameters from the user.
        if(reason=="client disconnected" and len(self.input_command)!=0):
            self.session_close_flag=0
        else:
            if(self.session_close_flag==0 and reason=="websocket closed"):
                pass
            else:
                self.clean_up(reason)
                
        logging.info('Connection to {}:{} lost'.format(*self.dst_addr))

        
