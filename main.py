from network2 import Session, BrainSession
import os
import time
import base64
import time

def my_channel(ch_name):
	return 'SIMPLEBIT_' + ch_name

def debug_handler(timestamp, user_name, message):
	print(f'{timestamp} | {user_name} | {message}\n')

def passer(timestamp, user_name, message):
	pass



if __name__ == '__main__':
	ch = 'b'
	user1 = 'alice'
	user2 = 'bob'

	BrainSession(ch).connect()



