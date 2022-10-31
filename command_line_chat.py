from threading import Thread
from datetime import datetime
from network import connect, send

# convert timestamp to iso date time format
def timestamp_to_iso(timestamp):
    return datetime.fromtimestamp(timestamp / 1000)\
        .isoformat().replace('T', ' ').split('.')[0]

def send_message():
    while True: send(input())

def react_on_messages(timestamp, user, message):
    time = timestamp_to_iso(timestamp)
    print(f'\n{time} {user}\n{message}\n')

user = input('Your name: ')
channel = input ('Channel to join or create: ')
# connect to (or create) a channel, with a user name
connect(channel, user, react_on_messages)
# start non-blocking thread to input and send messages
Thread(target = send_message).start()