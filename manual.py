# 手動実行用
from tkinter import *
from tkinter import ttk


root = Tk()
root.title('Schedule_Bot')

# ウィジェットの作成
frame1 = ttk.Frame(root, padding=16)
label1 = ttk.Label(frame1, text='1.送信テキスト入力')
t = StringVar()
entry1 = ttk.Entry(frame1, textvariable=t)
button1 = ttk.Button(
    frame1,
    text='OK',
    command=lambda: print('Hello, %s.' % t.get()))

# レイアウト
frame1.pack()
label1.pack(side=LEFT)
entry1.pack(side=LEFT)
button1.pack(side=LEFT)

# ウィンドウの表示開始
root.mainloop()
