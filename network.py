# SSE system for direct messaging
# [sends messages via sse.nodehill.com]

# Usage:
# from network_brython import connect, send, close

# connect(channel, user, event_handler)
#
#  Opens the network connection
#  - creates a channel if it doesn't exists
#  - joins the channel
#  - registers a function that will get all messages
#
#  Arguments:
#  * channel        string
#  * user           string
#  * handler        function that will receive
#				    (timestamp, user_name, message)
#                   * timestamp = milliseconds 
#                      since new years eve 1970 GMT
#                   * user_name - string
#                   * message - any 
#                      JSON serializable data type
#

# send(message) 
#    
#  Sends a message
#
#  Argument:
#  * message 	    any JSON serializable data type

# close()
# 
#  Closes the network connection

import json
import urllib.parse
import requests
from threading import Thread
from sseclient import SSEClient

close_it = False
channel_name = None
user_name = None 
token = None
message_handler = None
last_message_time = 0
serverURL = 'https://sse.nodehill.com'

def on_token(e):
	global token
	token = json.loads(e.data)

def on_message(e):
    global last_message_time
    try:
        d = json.loads(e.data)
        timestamp = d['timestamp']
        if not isinstance(timestamp, int):
            return
        last_message_time = timestamp
        user = d['user']
        message = d['data']
        message_handler(timestamp, user, message)
    except Exception as e: 
        return

def on_error(e):
    print('error')
    print(e.data)

def loop(channel, user, handler):
  global close_it, channel_name, user_name, message_handler
  message_handler = handler
  channel_name = urllib.parse.quote(channel)
  user_name = urllib.parse.quote(user)
  client = SSEClient(f'{serverURL}/api/listen/{channel_name}/' +
		f'{user_name}/{last_message_time}')
  for msg in client:
      if close_it:
        client.resp.close()
        close_it = False
        break
      elif msg.event == 'token' : 
        on_token(msg)
      elif msg.event == 'message':
        on_message(msg)
      elif msg.event == 'error':
        on_error(msg)

def connect(channel, user, handler):
    Thread(target = loop, args = (channel, user, handler)).start()

def send(message):
    requests.post(
        f'{serverURL}/api/send/{token}', 
        headers={'Content-type': 'application/json'},
        data=json.dumps({'message': message})
    )

def close():
    global close_it
    close_it = True
    send('Bye!')