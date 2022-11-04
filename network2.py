# SSE system for direct messaging
# [sends messages via sse.nodehill.com]
# ----Alternative context-manager based version!---- 


import json
import urllib.parse
import requests
import time
from threading import Thread
from sseclient import SSEClient
from collections import defaultdict
import re


class Session:
    SERVER_URL = 'https://sse.nodehill.com'

    def __init__(self, channel, user):
        self.channel = channel
        self.user = user

        self.close_it = False
        self.token = None
        self.last_message_time = 0
        self.last_exception = None
        self._message_handlers = defaultdict(defaultdict(list))

    def handler(self, timestamp, user, message):
        for pattern, priority_dict in self._message_handlers.items():
            if (m := pattern.match(message)):
                for _, funcs in sorted(priority_dict.items()):
                    for func in funcs:
                        func(m, timestamp, user, message)

    def on_message_pattern(self, pattern, priority=10):
        def inner_on_message_pattern(f):
            self._message_handlers[pattern][priority].append(f)
            def wrapped(m, timestamp, user, message):
                return f(m, timestamp, user, message)
            return wrapped
        return inner_on_message_pattern

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
            self.handler(timestamp, user, message)
        except Exception as e:
            # this is what I assume is just the keepalive ping wrongly treated as a message
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
            print(e)
            self.last_exception = e

    def connect(self):
        Thread(target=self.loop).start()

        while not self.last_exception and not self.token:
            time.sleep(1)

        # pick up other threada exception if it occured
        if (tmp := self.last_exception) is not None:
            self.last_exception = None
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
    REQUEST_PROVIDE_DIR_PATTERN = re.compile(fr'^REQUEST {USER_PATTERN_PART} PROVIDE_DIR$')
    GIVE_PROVIDE_DIR_PATTERN = re.compile(fr'^GIVE {USER_PATTERN_PART} PROVIDE_DIR (.+)$')

    def __init__(self, channel, user):
        super().__init__(channel, user)

        self.users = []
        self.provide_dir = 'foo'

        self.usersvar = None

    @Session.on_message_pattern(JOIN_PATTERN)
    def add_user(self, m, timestamp, user, message):
        self.users.append(m.group(1))

    @on_message_pattern(LEAVE_PATTERN)
    def remove_user(self, m, timestamp, user, message):
        self.users.remove(m.group(1))

    @on_message_pattern(JOIN_PATTERN, priority=11)
    @on_message_pattern(LEAVE_PATTERN, priority=11)
    def gui_update_users(self, m, timestamp, user, message):
        self.usersvar.set(self.users)

    @on_message_pattern(REQUEST_PROVIDE_DIR_PATTERN)
    def send_request_provide_dir(self, m, timestamp, user, message):
        if m.group(1) == self.user:
            send(f'GIVE {user} PROVIDE_DIR {self.provide_dir}')

    @on_message_pattern(GIVE_PROVIDE_DIR_PATTERN)
    def send_give_provide_dir(self, m, timestamp, user, message):
        if m.group(1) == self.user:
            # TODO
            print(m.group(2))
