from tkinter import *
import tkinter.messagebox as tkms
from tkinter import filedialog

root = Tk()

def buttonCallBack():
    tkms.showinfo("Hey", "U Clicked me!")

def fileDialog():
    filename = filedialog.askopenfilename(
        initialdir="/", title="Select A File", filetype=(("Accepted Media Files", "*.mjpeg"), ("All files", "*.*")))
    label = Label(labelFrame, text="")
    label.grid(column=1, row=3)
    label.configure(text=filename)

myLabel1 = Label(root, text="Hello World!", bg="red", fg="blue")
myLabel2 = Label(root, text="My name's Danh")

myLabel1.grid(row=0, column=0)
myLabel2.grid(row=2, column=0)


# myButton = Button(root, text="Click here", padx=10, pady=5, command=buttonCallBack)


# myButton.place(bordermode=OUTSIDE, height=100, width=100, relx=.5, rely=.5)


labelFrame = LabelFrame(root, text="Open File")
labelFrame.grid(column=1, row=1, padx=20, pady=20)
labelFrame.button = Button(
root, text="Browse A File", command=fileDialog).grid(column=1, row=2)




root.mainloop()

