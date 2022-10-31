# SSE system for direct messaging
# [sends messages via sse.nodehill.com]
# ----Alternative context-manager based version!---- 


import json
import urllib.parse
import requests
import time
from threading import Thread
from sseclient import SSEClient
import re


class Session:
    SERVER_URL = 'https://sse.nodehill.com'

    def __init__(self, channel, user, handler):
        self.channel = channel
        self.user = user
        self.message_handler = handler

        self.close_it = False
        self.token = None
        self.last_message_time = 0
        self.last_exception = None

    def on_token(self, e):
        self.token = json.loads(e.data)

    def on_message(self, e):
        try:
            d = json.loads(e.data)
            timestamp = d['timestamp']
            if not isinstance(timestamp, int):
                return
            self.last_message_time = timestamp
            user = d['user']
            message = d['data']
            self.message_handler(timestamp, user, message)
        except Exception as e:
            # this is just the keepalive ping wrongly treated as a message
            if str(e) != 'Expecting value: line 1 column 1 (char 0)':
                raise e

    def on_error(self, e):
        print('error')
        print(e.data)        

    def loop(self):
        try: 
            channel_name = urllib.parse.quote(self.channel)
            user_name = urllib.parse.quote(self.user)
            client = SSEClient(f'{self.SERVER_URL}/api/listen/{channel_name}/' +
                               f'{user_name}/{self.last_message_time}')
            for msg in client:
                if self.close_it:
                    client.resp.close()
                    self.close_it = False
                    self.token = None
                    break
                elif msg.event == 'token': 
                    self.on_token(msg)
                elif msg.event == 'message':
                    self.on_message(msg)
                elif msg.event == 'error':
                    self.on_error(msg)
        except Exception as e:
            self.last_exception = e

    def connect(self):
        Thread(target=self.loop).start()

        while not self.last_exception and not self.token:
            time.sleep(1)

        if (tmp := self.last_exception) is not None:
            print(tmp)
            self.last_exception = None
            print(tmp)
            return tmp

    def send(self, message):
        try:
            requests.post(
                f'{self.SERVER_URL}/api/send/{self.token}', 
                headers={'Content-type': 'application/json'},
                data=json.dumps({'message': message})
            )
        except Exception as e:
            # we don't handle this yet in gui so just print for now
            print(e)
            return e

    def close(self):
        self.close_it = True
        self.send('Bye!')

        while self.token:
            time.sleep(1)

    def __enter__(self):
        self.connect()
        return self;

    def __exit__(self, type, value, traceback):
        self.close()


class SimplebitSession(Session):
    USER_PATTERN_PART = r'([\w\d]+)'
    JOIN_PATTERN = re.compile(fr"""^User {USER_PATTERN_PART} joined channel (?:'|")(.+)(?:'|").$""")
    LEAVE_PATTERN = re.compile(fr"""^User (?:'|"){USER_PATTERN_PART}(?:'|") left channel (?:'|")(.+)(?:'|").$""")
    REQUEST_PROVIDE_DIR_PATTERN = re.compile(fr'REQUEST {USER_PATTERN_PART} PROVIDE_DIR')
    REQUEST_PROVIDE_DIR_PATTERN = re.compile(fr'GIVE {USER_PATTERN_PART} PROVIDE_DIR')


    #PATTERNS = [USER_PATTERN, JOIN_PATTERN, LEAVE_PATTERN, REQUEST_PROVIDE_DIR_PATTERN]

    def __init__(self, channel, user):
        self.channel = 'SIMPLEBIT_' + channel
        self.user = user
        self.handler = self.sb_handler
        super().__init__(self.channel, self.user, self.sb_handler)

        self.peer_model = {}
        self.users = []
        self.provide_dir = 'foo'
        self.receive_dir = 'bar'


    def sb_handler(self, timestamp, user, message):
        if (m := self.JOIN_PATTERN.match(message)):
            self.add_user(m.group(1))
        elif (m := self.LEAVE_PATTERN.match(message)):
            self.remove_user(m.group(1))
        elif (m := self.REQUEST_PROVIDE_DIR_PATTERN.match(message)):
            self.send_give_provide_dir(m.group(1))
        elif (m := self.GIVE_PROVIDE_DIR_PATTERN.match(message)):
            self.send_give_provide_dir(m.group(1))

    def add_user(self, user):
        if user != self.user: 
            self.users.append(user)

    def remove_user(self, user):
        if user != self.user:
            self.users.remove(user)

    def send_request_provide_dir(self, someone):
        send(f'REQUEST {someone} PROVIDE_DIR')

    def send_give_provide_dir(self, someone):
        send(f'GIVE {someone} PROVIDE_DIR {self.provide_dir}')
