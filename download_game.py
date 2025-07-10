import sys
import json
import tkinter as tk
from threading import Thread, Event
from tkinter import ttk

from SFTP_CLIENT import Sftp, ManualCancel

json_file = sys.argv[1]
print("reading...")
with open(json_file, encoding='UTF-8') as file:
    data = json.load(file)

base_remote_path = data['base_remote_path']
base_local_path = data['base_local_path']
main_window = tk.Tk()
progress = tk.IntVar()

is_canceled = Event()

# init tk components
main_window.title(f"copy {base_remote_path} to {base_local_path}")
progressbar = ttk.Progressbar(variable=progress)
progressbar.place(x=30, y=60, width=200)
main_window.geometry("300x200")


def set_progress(step, total):
    per = step / total
    if is_canceled.is_set():
        print("bye!")
        raise ManualCancel("download canceled by user")
    else:
        progress.set(per * 100)


def download_file():
    client = Sftp()
    client.download(base_remote_path, base_local_path, callback=set_progress)
    client.disconnect()
    print("finished!")
    main_window.quit()


def on_close():
    is_canceled.set()


# ForkThread
download_thread:Thread = Thread(
    target=download_file,
)
download_thread.start()

main_window.protocol('WM_DELETE_WINDOW', on_close)
main_window.mainloop()
download_thread.join()