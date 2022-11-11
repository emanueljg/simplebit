# SSE system for direct messaging
# [sends messages via sse.nodehill.com]
# ----Alternative class-based version!---- 


import os
import base64
from os import listdir
from os.path import isfile, join
import yaml
import json
import urllib.parse
import requests
import time
from threading import Thread
from sseclient import SSEClient
from collections import defaultdict
import re


def get_default_download_dir():
    return f"{os.getenv('USERPROFILE')}\\Downloads" \
             if os.name == 'nt' \
           else f"{os.getenv('HOME')}/Downloads" 

def get_file_files(dir_path):
    return [f for f in listdir(dir_path) if isfile(join(dir_path, f))] \
           if dir_path != '' else []

def ms_since_epoch():
    return time.time_ns() // 1000000


# evil metaclass hack that injects decorator functionality
class HookRegistrar(type):
    # use lambda to make a defaultdict of defaultdict values 
    # since defaultdict requires a callable
    hooks = defaultdict(lambda: defaultdict(list))  

    @classmethod
    def __prepare__(metacls, name, bases):
        def hook(pattern, priority=10):
            def inner_hook(f):
                HookRegistrar.hooks[pattern][priority].append(f)
                def wrapped(*args, **kwargs):
                    return f(*args, **kwargs)
                return wrapped
            return inner_hook
        
        return {'hook': hook, 'hooks': HookRegistrar.hooks}


class Session(metaclass=HookRegistrar):
    SERVER_URL = 'https://sse.nodehill.com'

    def __init__(self, channel, user):
        self.channel = channel
        self.user = user

        self.close_it = False
        self.token = None
        self.last_message_time = 0
        self.last_exception = None
        self.last_connected_at = None

    def handler(self, timestamp, user, message):
        if timestamp > self.last_connected_at:
            for pattern, priority_dict in self.hooks.items():
                if (m := pattern.match(message)):
                    for _, funcs in sorted(priority_dict.items()):
                        for func in funcs:
                            func(self, m, timestamp, user, message)

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
            print(e)
            return e

    def close(self):
        self.close_it = True
        self.send('Bye!')

        while self.token:
            time.sleep(1)

        self.last_connected_at = None

        self.user_files = {}
        self.update_users()
        self.current_selected_user = None
        self.filesvar.set([])

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
    PING_ALL_PATTERN = re.compile(fr'^PING_ALL$')
    PONG_PATTERN = re.compile(fr'^PONG {USER_PATTERN_PART}$')
    REQUEST_FILES_LIST_PATTERN = re.compile(fr'^REQUEST_FILES_LIST {USER_PATTERN_PART}$')
    GIVE_FILES_LIST_PATTERN = re.compile(fr'^GIVE_FILES_LIST {USER_PATTERN_PART} (.+)$')
    REQUEST_FILE_PATTERN = re.compile(fr'^REQUEST_FILE {USER_PATTERN_PART} (.+)$')
    GIVE_FILE_PATTERN = re.compile(fr'^GIVE_FILE {USER_PATTERN_PART} (.+) (.+)$')

    def __init__(self, channel, user):
        super().__init__(channel, user)
        self.user_files = {}
        
        self.provide_dir = None
        self.receive_dir = None
        self.load_settings()

        self.usersvar = None
        self.filesvar = None

        self.current_selected_user = None

    def load_settings(self):
        settings = None
        with open('settings.yml', 'r') as f:
            settings = yaml.safe_load(f)
        self.provide_dir = settings['provide_dir']
        self.receive_dir = settings['receive_dir']

    def save_settings(self):
        with open('settings.yml', 'w') as f:
            yaml.dump(
                {'provide_dir': self.provide_dir,
                 'receive_dir': self.receive_dir},
                f,
                allow_unicode=True)

    @property
    def files(self):
        return [f for f in listdir(self.provide_dir) 
                  if isfile(join(self.provide_dir, f))] \
          if self.provide_dir != '' else []

    def on_token(self, e):
        super().on_token(e)
        if self.last_connected_at is None: 
            self.last_connected_at = ms_since_epoch()
            self.send_ping_all()

    def update_users(self):
        self.usersvar.set(list(self.user_files.keys()))

    def update_files(self, user):
        self.current_selected_user = user
        self.filesvar.set(self.user_files.get(user, []))

    def send_ping_all(self):
        self.send('PING_ALL')

    @hook(PING_ALL_PATTERN)
    def pong(self, m, timestamp, user, message):
        if user != self.user:
            self.user_files[user] = []
            self.update_users()
            self.send(f'PONG {user}')

    @hook(PONG_PATTERN)
    def register_pongs(self, m, timestamp, user, message):
        if m.group(1) == self.user:
            self.user_files[user] = []
            self.update_users()

    @hook(LEAVE_PATTERN)
    def remove_user(self, m, timestamp, user, message):
        del self.user_files[m.group(1)]
        self.update_users()
        if self.current_selected_user not in self.user_files:
            self.filesvar.set([])

    def send_request_files_list(self, user):
        self.send(f'REQUEST_FILES_LIST {user}')

    @hook(REQUEST_FILES_LIST_PATTERN)
    def send_give_files_list(self, m, timestamp, user, message):
        if m.group(1) == self.user:
            self.send(f'GIVE_FILES_LIST {user} {json.dumps(self.files)}')

    @hook(GIVE_FILES_LIST_PATTERN)
    def accept_files_list(self, m, timestamp, user, message):
        if m.group(1) == self.user:
            self.user_files[user] = json.loads(m.group(2))
            self.update_files(user)

    def send_request_file(self, user, file):
        self.send(f'REQUEST_FILE {user} {file}')

    @hook(REQUEST_FILE_PATTERN)
    def send_give_file(self, m, timestamp, user, message):
        print('got it')
        if m.group(1) == self.user:
            file_name = m.group(2)
            file_path = os.path.join(self.provide_dir, file_name)
            file_string = 'DATA_UNSET'  # default to unhappy path
            with open(file_path, 'rb') as f:
                file_string = base64.b64encode(f.read()).decode('ascii')
            self.send(f'GIVE_FILE {user} {file_name} {file_string}')

    @hook(GIVE_FILE_PATTERN)
    def accept_file(self, m, timestamp, user, message):
        if m.group(1) == self.user:
            dl_dir = self.receive_dir \
                       if self.receive_dir != '' \
                     else get_default_download_dir()
            file_name = m.group(2)
            file_path = os.path.join(dl_dir, file_name)
            data = m.group(3)
            with open(file_path, 'wb') as f:
                f.write(base64.b64decode(data))
