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

#datetime is used to deal with timestamps
from datetime import datetime
#re is used to search for command status and time.
import re
#sqlite3 is used to manage a disk based database.
import sqlite3

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

        #visualize bit is for the visualization of the interactive command execution.
        #This visualization can be seen in the place where the application is launched.
        self.visualize_bit=0
        #For checking tmux.Assume tmux is present by default
        self.tmux_bit=1
        #The four components of a command sent for interactive execution.
        self.input_command=None
        self.command_id=None
        self.entry_timestamp=None
        self.session_id=None

    def __call__(self, fd, events):
        if events & IOLoop.READ:
            self.on_read()
        if events & IOLoop.WRITE:
            self.on_write()
        if events & IOLoop.ERROR:
            self.close(reason='error event occurred')
    
    #to extract the command execution status and time taken to execute the comand
    def get_time_status(self,t):
        command_status,execution_time,cst=None,None,None
        cst=re.search(self.command_id+':Status=[0-9]{1,3}',t)     
        if(cst):
            timepos=re.search(r"time\-",t[cst.start():]).start()
            uscpos=re.search(r"\_",t[cst.start()+timepos:]).start()
            epoch=int(t[cst.start()+timepos+5:cst.start()+timepos+uscpos])
            exit_time=int(epoch)
            entry_time=self.entry_timestamp
            execution_time=str(exit_time-entry_time)+"s"
            equal_pos=re.search("=",t[cst.start():cst.end()]).start()
            command_status=t[cst.start()+equal_pos+1:cst.end()]
        return command_status,execution_time
            
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
            #For terminal visualization
            if(self.visualize_bit):
                print(data.decode())
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
                if(self.input_command):
                    #obtain command execution status and time
                    command_status,execution_time=self.get_time_status(data.decode())
                    #if status and time is obtained
                    if(command_status and execution_time):
                        #The result of the interactive execution. Encode and send to the client.
                        result_string='{"session":"%s","id":"%s","command":"%s","status":"%s","time":"%s","timestamp":"%s"}'%(
                            self.session_id,self.command_id,self.input_command,command_status,execution_time,str(datetime.fromtimestamp(self.entry_timestamp)))
                        self.handler.write_message(result_string)
                        #To clear inserted command to enable entry of next
                        self.input_command=None
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
        
        #Record the entry timestamp of the command for a particular session when a disconnection happens
        if(self.input_command and self.tmux_bit):
            try:
                #Connect to disk database
                con=sqlite3.connect("entry_time_backup.db")
                cur=con.cursor()
                #Check if there already is an entry for the session.
                s1=cur.execute("select timestamp from entry_time_table where session_id=?",(self.session_id,))
                #If not, insert a new entry.
                if(s1.fetchall()==[]):
                    cur.execute("insert into entry_time_table values (?,?)",(self.session_id,self.entry_timestamp))
                #If present, update entry with new timestamp.
                else:
                    cur.execute("update entry_time_table set timestamp=? where session_id=?",(self.entry_timestamp,self.session_id))
                con.commit()
                con.close()
            except sqlite3.OperationalError as e:
                logging.info(e)
                return
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
        logging.info('Connection to {}:{} lost'.format(*self.dst_addr))

        clear_worker(self, clients)
        logging.debug(clients)

        
