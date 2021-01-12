from tkinter import *

top = Tk()
top.geometry('500x250')

top_frame = LabelFrame(top, text="My Frame")

label = Label(top_frame, text="User Name")
label.grid(row=1, column=0, pady=(20, 20))
label.config(state=DISABLED)

entry = Entry(top_frame, bd=5)
entry.grid(row=1, column=1)
entry.config(state=DISABLED)

var1 = IntVar()


def activateCheck():
    if var1.get() == 1:  # whenever checked
        label.config(state=NORMAL)
        entry.config(state=NORMAL)
    elif var1.get() == 0:  # whenever unchecked
        label.config(state=DISABLED)
        entry.config(state=DISABLED)


cb = Checkbutton(top, text="Save Image", variable=var1, command=activateCheck)
cb.grid(row=0)

top.mainloop()