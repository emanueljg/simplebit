from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from network2 import SimplebitSession


BS = SimplebitSession('', '')

users = []


root = Tk()
root.title('Simplebit')
root.grid_columnconfigure(0, weight=1)
root.grid_rowconfigure(0, weight=1)

c = ttk.Frame(root)
c.grid(row=0, column=0, padx=5, pady=5, sticky=(N,W,E,S))
c.rowconfigure(2, weight=1)
c.columnconfigure(2, weight=1)

def on_user_select(evt):
    w = evt.widget
    if len(cs := w.curselection()) > 0:
        index = int(cs[0])
        user = w.get(index)
        BS.send_request_files_list(user)

def on_file_select(evt):
    w = evt.widget
    if len(cs := w.curselection()) > 0:
        index = int(cs[0])
        file = w.get(index)
        BS.send_request_file(BS.current_selected_user, file)

usersvar = StringVar()
userbox = Listbox(c, listvariable=usersvar)
userbox.bind('<<ListboxSelect>>', on_user_select)
userbox.grid(row=2, column=1, padx=(0, 10), sticky='nsw')

filesvar = StringVar()
filesbox = Listbox(c, listvariable=filesvar)
filesbox.bind('<<ListboxSelect>>', on_file_select)
filesbox.grid(row=2, column=2, sticky='nswe')

BS.usersvar = usersvar
BS.filesvar = filesvar

def onselect(evt):
    # Note here that Tkinter passes an event object to onselect()
    w = evt.widget
    if len(cs := w.curselection()) > 0:
        print(cs)
        index = int(w.curselection()[0])
        print(index)
        value = w.get(index)
        print(value)

menu = ttk.Frame(c) 
menu.grid(row=1, column=1, columnspan=2, pady=10, sticky='W')


channelvar = StringVar()
usernamevar = StringVar()
connection_status_var = StringVar(value='Not connected.')
connection_button_var = StringVar(value='Connect')

provide_dir_var = StringVar(value=BS.provide_dir)
receive_dir_var = StringVar(value=BS.receive_dir)

def update_users():
    usersvar.set(BS.users)


def show_connection_dialog():


    def dismiss():
        dlg.grab_release()
        dlg.destroy()

    dlg = Toplevel(root)
    dlg.geometry('300x200')
    #dlg.grid_columnconfigure(0, weight=0)
    dlg.grid_columnconfigure(1, weight=1)

    channel_lbl = ttk.Label(dlg, text='Channel: ')  
    channel_entry = ttk.Entry(dlg, textvariable=channelvar)
    username_lbl = ttk.Label(dlg, text='Username:')
    username_entry = ttk.Entry(dlg, textvariable=usernamevar)

    connection_status_label = ttk.Label(dlg, textvariable=connection_status_var, wraplength=300)

    def apply():
        if connection_button_var.get() != 'Disconnect':  # treat as connect button
            # 
            BS.channel = channelvar.get()
            BS.user    = usernamevar.get()
            ret = BS.connect()
            if ret is None:  # happy path
                connection_status_var.set(f'Connected! Token: {BS.token}')
                connection_button_var.set('Disconnect')
                # update_users()
            else:
                connection_status_var.set(f'Error! {ret}')
        else:  
            BS.close()
            connection_status_var.set('Not connected.') 
            connection_button_var.set('Connect')

    apply_btn = ttk.Button(dlg, textvariable=connection_button_var, command=apply)
    cancel_btn = ttk.Button(dlg, text='Close', command=dismiss)


    channel_lbl.grid(row=0, column=0, padx=10, pady=10, sticky='W')
    channel_entry.grid(row=0, column=1, sticky='WE')
    username_lbl.grid(row=1, column=0, padx=10, sticky='W')
    username_entry.grid(row=1, column=1, sticky='WE')
    connection_status_label.grid(row=2, column=0, columnspan=2, padx=10, pady=20, sticky='W')
    apply_btn.grid(row=3, column=0, padx=10, sticky='W')
    cancel_btn.grid(row=3, column=1, sticky='W')


def show_settings_dialog():
    def choose_provide_dir():
        provide_dir_var.set(filedialog.askdirectory())

    def choose_receive_dir():
        receive_dir_var.set(filedialog.askdirectory())

    def save_settings():
        BS.provide_dir = provide_dir_var.get()
        BS.receive_dir = receive_dir_var.get()
        BS.save_settings()

    def dismiss():
        provide_dir_var.set(BS.provide_dir)
        receive_dir_var.set(BS.receive_dir)
        dlg.grab_release()
        dlg.destroy()

    dlg = Toplevel(root)
    dlg.geometry('500x400')
    #dlg.grid_columnconfigure(0, weight=0)
    dlg.grid_columnconfigure(1, weight=1)

    provide_dir_lbl = ttk.Label(dlg, text='Provide directory:')
    provide_dir_btn = ttk.Button(dlg, text='Choose', command=choose_provide_dir)
    provide_dir_entry = ttk.Entry(dlg, textvariable=provide_dir_var)

    receive_dir_lbl = ttk.Label(dlg, text='Receive directory:')
    receive_dir_btn = ttk.Button(dlg, text='Choose', command=choose_receive_dir)
    receive_dir_entry = ttk.Entry(dlg, textvariable=receive_dir_var)

    apply_btn = ttk.Button(dlg, text='Apply', command=save_settings)
    cancel_btn = ttk.Button(dlg, text='Close', command=dismiss)


    provide_dir_lbl.grid(row=0, column=0, padx=(5, 10), pady=(10, 0), sticky='W')   
    provide_dir_btn.grid(row=0, column=1, pady=(10, 0), sticky='W')
    provide_dir_entry.grid(row=1, column=0, padx=(20, 10), pady=(5, 20), columnspan=2, sticky='WE')

    receive_dir_lbl.grid(row=2, column=0, padx=(5, 10), pady=(10, 0), sticky='W')   
    receive_dir_btn.grid(row=2, column=1, pady=(10, 0), sticky='W')
    receive_dir_entry.grid(row=3, column=0, padx=(20, 10), pady=(5, 35), columnspan=2, sticky='WE')



    apply_btn.grid(row=4, column=0, padx=(5, 0))
    cancel_btn.grid(row=4, column=1, padx=(5, 0), sticky='W')


    dlg.protocol("WM_DELETE_WINDOW", dismiss) # intercept close button
    dlg.transient(root)   # dialog window is related to main
    dlg.wait_visibility() # can't grab until window appears, so we wait
    dlg.grab_set()        # ensure all input goes to our window

join_menu_button = ttk.Button(menu, text='Connection', command=show_connection_dialog)
join_menu_button.grid(row=0, column=0, padx=(0, 10))

settings_menu_button = ttk.Button(menu, text='Settings', command=show_settings_dialog)
settings_menu_button.grid(row=0, column=1)

root.mainloop()