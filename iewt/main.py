import logging
import tornado.web
import tornado.ioloop
from tornado.options import options
from iewt import handler
from iewt.handler import IEWTHandler, IndexHandler, WsockHandler, NotFoundHandler
from iewt.settings import (
    get_app_settings,  get_host_keys_settings, get_policy_setting,
    get_ssl_context, get_server_settings, check_encoding_setting
)

#sqlite3 is used to create a disk based database.
import sqlite3

def make_handlers(loop, options):
    host_keys_settings = get_host_keys_settings(options)
    policy = get_policy_setting(options, host_keys_settings)

    handlers = [
        #IEWT handler is to render the frontend(iewt.html).
        (r'/iewt', IEWTHandler),
        (r'/', IndexHandler, dict(loop=loop, policy=policy,
                                  host_keys_settings=host_keys_settings)),
        (r'/ws', WsockHandler, dict(loop=loop))
    ]
    return handlers


def make_app(handlers, settings):
    settings.update(default_handler_class=NotFoundHandler)
    return tornado.web.Application(handlers, **settings)


def app_listen(app, port, address, server_settings):
    app.listen(port, address, **server_settings)
    if not server_settings.get('ssl_options'):
        server_type = 'http'
    else:
        server_type = 'https'
        handler.redirecting = True if options.redirect else False
    logging.info(
        'Listening on {}:{} ({})'.format(address, port, server_type)
    )


def main():
    options.parse_command_line()
    check_encoding_setting(options.encoding)
    #For managing the disk database
    try:
        #create (or connect to) disk database
        con=sqlite3.connect("entry_time_backup.db")
        cur=con.cursor()
        #create (if not existing) table upon the disk database
        cur.execute("create table if not exists entry_time_table(session_id,timestamp)")
        con.close()
    except sqlite3.OperationalError as e:
        #If database creation fails, it is mostly because of privelege issue.
        logging.info(e+"\nFile creation required. Run application in a location with sufficient priveleges")
        return
    
    loop = tornado.ioloop.IOLoop.current()
    app = make_app(make_handlers(loop, options), get_app_settings(options))
    ssl_ctx = get_ssl_context(options)
    server_settings = get_server_settings(options)
    app_listen(app, options.port, options.address, server_settings)
    if ssl_ctx:
        server_settings.update(ssl_options=ssl_ctx)
        app_listen(app, options.sslport, options.ssladdress, server_settings)
    loop.start()


if __name__ == '__main__':
    main()

