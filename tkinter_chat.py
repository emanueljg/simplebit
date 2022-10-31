from threading import Thread
from datetime import datetime
from network import connect, send
import tkinter as tk
from tkinter.ttk import Frame, Label, Entry, Button
# Import or own functions that make creating windows easier
from window_handling import create_window, start_window_loop

# Create a window
win = create_window(tk, 'Chat', 70, 70)

# convert timestamp to iso date time format
def timestamp_to_iso(timestamp):
    return datetime.fromtimestamp(timestamp / 1000)\
        .isoformat().replace('T', ' ').split('.')[0]

def pack_widgets(*widgets):
    for widget in widgets: widget.pack(pady = 10)

def clear(max_length = 0):
    counter = len(win.winfo_children())
    input_field = None
    try:
        input_field = win.nametowidget('to_send')
    except: pass
    for widget in win.winfo_children():
        if len(win.winfo_children()) > max_length\
            and input_field != widget:
             widget.destroy()

def react_on_messages(timestamp, user, message): 
    clear(6) # max 6 latest messages on screen
    aframe = Frame(win)
    aframe.pack()
    pack_widgets(
        Label(aframe, text = f'{timestamp_to_iso(timestamp)} {user}'),
        Label(aframe, text = message)
    )

def start_chat():
    user = win.nametowidget('user').get()
    channel = win.nametowidget('channel').get()
    clear()
    connect(channel, user, react_on_messages)
    message = Entry(win, width = 30, name='to_send')
    message.pack(side=tk.BOTTOM)
    message.bind('<Return>', send_message)


def send_message(e):
    send(win.nametowidget('to_send').get())
    win.nametowidget('to_send').delete(0, tk.END)

# Initial widgets
pack_widgets(
    Label(win, text = ''),
    Label(win, text = 'Skapa ett användarnamn:'),
    Entry(win, width = 30, name = 'user'),
    Label(win, text = 'Välj en kanal (skapa eller gå med i)'),
    Entry(win, width = 30, name = 'channel'),
    Button(win, text = 'Börja chatta', command = start_chat),
)

# Show the window
start_window_loop(win)