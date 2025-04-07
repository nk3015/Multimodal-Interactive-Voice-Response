import tkinter as tk
from tkinter import messagebox
import pandas as pd
import pyttsx3
import speech_recognition as sr
import threading

def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        status_label.config(text="Listening...")
        root.update_idletasks()
        try:
            audio = recognizer.listen(source, timeout=5)
            text = recognizer.recognize_google(audio)  # Using Google Speech Recognition
            entry_var.set(text)  # Insert recognized text into the text field
            status_label.config(text="Done")
        except sr.UnknownValueError:
            status_label.config(text="Could not understand audio")
        except sr.RequestError:
            status_label.config(text="Speech Recognition service unavailable")
    root.after(1000, start_listening)

def start_listening():
    threading.Thread(target=recognize_speech, daemon=True).start()

# Load bank data
df = pd.read_excel("bank_data.xlsx")

# Initialize Text-to-Speech
engine = pyttsx3.init()

# Global variable for storing current user
current_user = None

# Function to speak after UI updates
def speak(text, delay=500):
    root.after(delay, lambda: engine.say(text) or engine.runAndWait())

# Function to validate phone number and start IVR
def validate_phone():
    phone = phone_entry.get()
    if len(phone) == 10 and phone.isdigit():
        phone_frame.pack_forget()
        ivr_frame.pack()  # Show IVR first
        speak("Welcome to ABC Bank. Press 1 for Traditional IVR, Press 2 for GUI.", 1000)
    else:
        messagebox.showerror("Error", "Please enter a valid 10-digit number.")

# Function to handle IVR keypress
def ivr_keypress(key):
    if key == "1":
        speak("Press 1 for Bank Statement, Press 2 for Credit Card Info, Press 3 for Offers Available.", 1000)
    elif key == "2":
        switch_to_gui()

# Function to switch to GUI
def switch_to_gui():
    ivr_frame.pack_forget()
    gui_frame.pack()

# Function to switch back to IVR
def switch_to_ivr():
    gui_frame.pack_forget()
    ivr_frame.pack()

# Function to handle Bank Statement button
def bank_statement():
    global current_user
    current_user = df.sample(n=1).iloc[0]  # Select a random user

    # Masked account number
    masked_account = f"XXXX-XXXX-{str(current_user['Account Number'])[-4:]}"

    # Display details
    account_entry.config(state="normal")
    account_entry.delete(0, tk.END)
    account_entry.insert(0, masked_account)
    account_entry.config(state="readonly")

    name_entry.config(state="normal")
    name_entry.delete(0, tk.END)
    name_entry.insert(0, current_user["User Name"])
    name_entry.config(state="readonly")

    sort_code_entry.delete(0, tk.END)

    gui_frame.pack_forget()
    bank_statement_frame.pack()
    speak("Please enter your sort code for verification.", 1000)

# Function to verify sort code
def verify_sort_code():
    entered_code = sort_code_entry.get()

    try:
        entered_code = int(entered_code)
    except ValueError:
        messagebox.showerror("Error", "Please enter a valid 6-digit sort code.")
        return

    if current_user is not None and entered_code == current_user["Sort Code"]:
        balance_text = f"Bank Balance: ${current_user['Bank Balance']}"
        transactions_list = eval(current_user["Last 3 Transactions"])
        transactions_text = "\n".join([f"Transaction: ${t}" for t in transactions_list])

        balance_label.config(text=balance_text)
        transactions_label.config(text=transactions_text)
        speak(balance_text, 1000)
        speak("Last 3 transactions are:", 2000)
        speak(transactions_text, 3000)
    else:
        messagebox.showerror("Error", "Incorrect Sort Code. Access Denied!")
        speak("Incorrect Sort Code. Access Denied!", 1000)

# GUI Setup
root = tk.Tk()
root.title("IVR Bank System")
root.geometry("400x600")
root.configure(bg="#2C3E50")

# Phone Entry Frame
phone_frame = tk.Frame(root, bg="#2C3E50")
phone_frame.pack()

tk.Label(phone_frame, text="Enter 10-digit Phone Number:", font=("Arial", 14), bg="#2C3E50", fg="white").pack(pady=10)
phone_entry = tk.Entry(phone_frame, font=("Arial", 14), width=15)
phone_entry.pack(pady=5)

call_btn = tk.Button(phone_frame, text="Call", font=("Arial", 14), bg="green", fg="white", command=validate_phone)
call_btn.pack(pady=10)

# IVR Frame
ivr_frame = tk.Frame(root, bg="#2C3E50")

buttons = [
    ['1', '2', '3'],
    ['4', '5', '6'],
    ['7', '8', '9'],
    ['*', '0', '#']
]

for i, row in enumerate(buttons):
    for j, num in enumerate(row):
        btn = tk.Button(ivr_frame, text=num, width=5, height=2, font=("Arial", 14), bg="#3498DB", fg="white",
                        command=lambda n=num: ivr_keypress(n))
        btn.grid(row=i, column=j, padx=5, pady=5)

ivr_to_gui_btn = tk.Button(ivr_frame, text="Switch to GUI", font=("Arial", 12), bg="#E67E22", fg="white", command=switch_to_gui)
ivr_to_gui_btn.grid(row=4, column=1, pady=10)

# GUI Frame
gui_frame = tk.Frame(root, bg="#2C3E50")

options = [("Bank Statement", bank_statement), ("Credit Card Info", lambda: speak("Credit Card Info", 1000)), 
           ("Offers Available", lambda: speak("Offers Available", 1000))]

for text, command in options:
    btn = tk.Button(gui_frame, text=text, font=("Arial", 14), width=25, height=2, 
                    bg="#E67E22", fg="white", command=command)
    btn.pack(pady=10)

gui_to_ivr_btn = tk.Button(gui_frame, text="Switch to IVR", font=("Arial", 12), bg="#E74C3C", fg="white", command=switch_to_ivr)
gui_to_ivr_btn.pack(pady=10)

# Bank Statement Frame
bank_statement_frame = tk.Frame(root, bg="#2C3E50")

tk.Label(bank_statement_frame, text="Account Number:", font=("Arial", 14), bg="#2C3E50", fg="white").pack(pady=5)
account_entry = tk.Entry(bank_statement_frame, font=("Arial", 14), width=20, state="readonly")
account_entry.pack(pady=5)

tk.Label(bank_statement_frame, text="Name:", font=("Arial", 14), bg="#2C3E50", fg="white").pack(pady=5)
name_entry = tk.Entry(bank_statement_frame, font=("Arial", 14), width=20, state="readonly")
name_entry.pack(pady=5)

tk.Label(bank_statement_frame, text="Enter Sort Code:", font=("Arial", 14), bg="#2C3E50", fg="white").pack(pady=5)
sort_code_entry = tk.Entry(bank_statement_frame, font=("Arial", 14), width=15)
sort_code_entry.pack(pady=5)

verify_btn = tk.Button(bank_statement_frame, text="Verify", font=("Arial", 14), bg="green", fg="white",
                       command=verify_sort_code)
verify_btn.pack(pady=10)

balance_label = tk.Label(bank_statement_frame, text="", font=("Arial", 14), bg="#2C3E50", fg="white")
balance_label.pack(pady=5)

transactions_label = tk.Label(bank_statement_frame, text="", font=("Arial", 12), bg="#2C3E50", fg="white")
transactions_label.pack(pady=5)

status_label = tk.Label(root, text="Starting voice recognition...")
status_label.pack()

# Start listening immediately
root.after(1000, start_listening)

root.mainloop()