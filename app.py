from tornado import websocket, web, ioloop
import json
import threading
import sys
import time
import os
import logging

from watchdog.observers import Observer
from watchdog.events import RegexMatchingEventHandler

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.FileHandler('exp-watcher.log')
handler.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s: %(name)s ~ %(levelname)s: %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)

cl = list()


class IndexHandler(web.RequestHandler):
    def get(self):
        self.render("index.html")


class SocketHandler(websocket.WebSocketHandler):
    def check_origin(self, origin):
        return True

    def open(self):
        if self not in cl:
            cl.append(self)

    def on_close(self):
        if self in cl:
            cl.remove(self)


class ApiHandler(web.RequestHandler):

    @web.asynchronous
    def get(self, *args):
        self.finish()
        _id = self.get_argument("id")
        value = self.get_argument("value")
        data = {"id" : _id, "value" : value}
        data = json.dumps(data)
        for c in cl:
            c.write_message(data)

    @web.asynchronous
    def post(self):
        pass


class ImageWatcher:
    def __init__(self, src_path):
        self.__src_path = src_path
        self.__event_handler = ImageHandler()
        self.__event_observer = Observer()

    def run(self):
        self.start()
        try:
            while True: 
                global stop_thread 
                if stop_thread: 
                    break
                time.sleep(1)
        except Exception:
            logger.exception("File watcher interrupted")
        finally:
            self.stop()

    def start(self):
        self.__schedule()
        self.__event_observer.start()
        logger.info('File watcher started!')

    def stop(self):
        self.__event_observer.stop()
        self.__event_observer.join()
        logger.info('File watcher stoped!')

    def __schedule(self):
        self.__event_observer.schedule(
            self.__event_handler,
            self.__src_path,
            recursive=True
        )


class ImageHandler(RegexMatchingEventHandler):
    # FILE_REGEX = [r".*\.fits$"]
    FILE_REGEX = [r".*"]

    def __init__(self):
        super().__init__(self.FILE_REGEX)


    def on_created(self, event):
        file_size = -1

        while file_size != os.path.getsize(event.src_path):
            file_size = os.path.getsize(event.src_path)
            time.sleep(2)

        filename = os.path.basename(event.src_path)
        logger.info("Welcome {} Image! :)".format(filename))

        for c in cl:
            c.write_message({'filename': filename})


exp = ImageWatcher('.')
stop_thread = False
t1 = threading.Thread(target=exp.run) 
t1.start() 

app = web.Application([
    (r'/', IndexHandler),
    (r'/ws', SocketHandler),
    (r'/api', ApiHandler),
    (r'/(favicon.ico)', web.StaticFileHandler, {'path': '../'}),
    (r'/(rest_api_example.png)', web.StaticFileHandler, {'path': './'}),
])

if __name__ == '__main__':
    app.listen(8888)
    ioloop.IOLoop.instance().start()
