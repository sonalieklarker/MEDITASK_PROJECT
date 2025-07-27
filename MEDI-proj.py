import tkinter as tk
from tkinter import messagebox, ttk
from pymongo import MongoClient
import datetime
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration (MongoDB URI and Email credentials)
MONGO_URI = "mongodb+srv://sonali:sonali1@project.6o303.mongodb.net/?retryWrites=true&w=majority"
DATABASE_NAME = "medi_task"
PATIENTS_COLLECTION = "patients"
TASKS_COLLECTION = "tasks"
EMAIL_USERNAME = "mtaasskk@gmail.com"
EMAIL_PASSWORD = "vtng jirf ajnu lqcm"
APP_TITLE = "Medi-Task: Healthcare Task Management"
WINDOW_WIDTH = 800  # Adjusted width
WINDOW_HEIGHT = 650  # Adjusted height

# Color palette for better visibility
BG_COLOR = "#ADD8E6"  # Light Blue
FG_COLOR = "#000000"  # Black
ENTRY_FG_COLOR = "#8B0000"  # Maroon for typing
ACCENT_COLOR = "#ADD8E6"  # Sky Blue
BUTTON_COLOR = "#ADD8E6"  # Sky Blue for Buttons
BUTTON_TEXT_COLOR = "#000000"  # Black for button text

# Font
TEXT_FONT = ("Times New Roman", 10)

# Database connection
def connect_to_mongodb():
    try:
        client = MongoClient(MONGO_URI)
        # Force a connection to the database
        client.admin.command('ping')
        logging.info("Connected to MongoDB successfully.")
        db = client[DATABASE_NAME]
        
        # Initialize collections
        global patients_collection, tasks_collection
        patients_collection = db[PATIENTS_COLLECTION]
        tasks_collection = db[TASKS_COLLECTION]
        
        return db
    except Exception as e:
        logging.error(f"Failed to connect to MongoDB: {e}")
        messagebox.showerror("Error", f"Failed to connect to the database: {e}")
        return None

# Email validation function
def is_valid_email(email):
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(email_pattern, email) is not None

# Send email function
def send_email(to_email, subject, body):
    try:
        # Sender's credentials
        from_email = EMAIL_USERNAME
        from_password = EMAIL_PASSWORD

        # Set up the server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()  # Secure the connection with TLS
        server.login(from_email, from_password)

        # Create the email message
        message = MIMEMultipart()
        message['From'] = from_email
        message['To'] = to_email
        message['Subject'] = subject
        message.attach(MIMEText(body, 'plain'))

        # Send the email
        server.sendmail(from_email, to_email, message.as_string())
        server.quit()  # Close the server connection

        logging.info(f"Email sent to {to_email} successfully.")
        return True
    except Exception as e:
        logging.error(f"Failed to send email: {e}")
        return False

# Database helper functions
def add_patient(patient_id, patient_name, email):
    """Adds a new patient to the database."""
    try:
        if not patient_id or not patient_name or not email:
            raise ValueError("Patient ID, name, and email are required.")

        # Validate email format
        if not is_valid_email(email):
            raise ValueError("Invalid email format.")

        existing_patient = patients_collection.find_one({"_id": patient_id})

        new_patient = {
            "_id": patient_id,  # Store the patient id as given
            "patient_name": patient_name,
            "email": email,
            "created_at": datetime.datetime.utcnow(),
        }

        if existing_patient:
            patients_collection.update_one({"_id": patient_id}, {"$set": new_patient})
            logging.info(f"Patient {patient_name} updated in the database.")
            messagebox.showinfo("Success", f"Patient {patient_name} updated successfully.")
            return True
        else:
            patients_collection.insert_one(new_patient)
            logging.info(f"Patient {patient_name} added to the database.")
            messagebox.showinfo("Success", f"Patient {patient_name} added successfully.")
            return True
    except ValueError as ve:
        logging.error(f"Validation error adding patient: {ve}")
        messagebox.showerror("Error", str(ve))
        return False
    except Exception as e:
        logging.error(f"Error adding patient: {e}")
        messagebox.showerror("Error", f"An unexpected error occurred: {e}")
        return False

def add_task(patient_id, task_name, start_time, end_time, priority, repeat_interval):
    """Adds a new task to the database."""
    try:
        # Validate inputs
        if not all([task_name, start_time, end_time, priority, repeat_interval, patient_id]):
            raise ValueError("All fields are required.")

        # Validate priority
        priority = int(priority)
        if not 1 <= priority <= 5:
            raise ValueError("Priority must be between 1 and 5.")

        # Convert start and end times to strings
        try:
            start_time_obj = datetime.datetime.strptime(start_time, "%H:%M").time()
            end_time_obj = datetime.datetime.strptime(end_time, "%H:%M").time()
            start_time_str = start_time_obj.strftime("%H:%M")  # Format as HH:MM string
            end_time_str = end_time_obj.strftime("%H:%M")  # Format as HH:MM string

        except ValueError:
            raise ValueError("Invalid time format. Please use HH:MM.")

        task_data = {
            "patient_id": patient_id,  # Reference by patient_id
            "task_name": task_name,
            "start_time": start_time_str,  # Store as string
            "end_time": end_time_str,  # Store as string
            "priority": priority,
            "repeat_interval": repeat_interval,
            "created_at": datetime.datetime.utcnow(),
        }

        tasks_collection.insert_one(task_data)
        logging.info(f"Task '{task_name}' added for patient {patient_id}.")
        messagebox.showinfo("Success", f"Task '{task_name}' added successfully.")
        return True

    except ValueError as ve:
        logging.error(f"Validation error adding task: {ve}")
        messagebox.showerror("Error", str(ve))
        return False
    except Exception as e:
        logging.error(f"Error adding task: {e}")
        messagebox.showerror("Error", f"Failed to add task: {e}")
        return False

def send_reminder_email(patient_id, task_name, start_time):
    """Sends a reminder email to the patient about the task."""
    try:
        patient = patients_collection.find_one({"_id": patient_id})
        if not patient:
            raise ValueError(f"Patient with ID {patient_id} not found.")

        email = patient["email"]
        subject = f"Reminder: {task_name} at {start_time}"
        body = f"Dear {patient['patient_name']},\n\nThis is a reminder for your task '{task_name}' scheduled at {start_time}."

        if send_email(email, subject, body):
            logging.info(f"Reminder email sent to {email} for task {task_name}.")
            messagebox.showinfo("Success", f"Reminder email sent to {email} for task '{task_name}'.")
        else:
            logging.error(f"Failed to send reminder email to {email}.")
            messagebox.showerror("Error", "Failed to send reminder email.")

    except Exception as e:
        logging.error(f"Failed to send email to patient id {patient_id}: {e}")
        messagebox.showerror("Error", f"Failed to send reminder email: {e}")
        return False

def view_priority_tasks():
    """View tasks ordered by priority."""
    try:
        # Fetch tasks sorted by priority (ascending order)
        tasks = list(tasks_collection.find().sort("priority", 1))  # Sorting by priority
        if not tasks:
            messagebox.showinfo("No Tasks", "No tasks available.")
            return

        # Create a new window for displaying tasks
        task_window = tk.Toplevel(root)
        task_window.title("View Priority Tasks")
        task_window.geometry("600x400")

        # Create a Treeview widget to display tasks
        task_tree = ttk.Treeview(task_window, columns=("Task Name", "Start Time", "End Time", "Priority"), show="headings")
        task_tree.pack(fill="both", expand=True, padx=10, pady=10)

        # Define headings
        task_tree.heading("Task Name", text="Task Name")
        task_tree.heading("Start Time", text="Start Time")
        task_tree.heading("End Time", text="End Time")
        task_tree.heading("Priority", text="Priority")

        # Insert tasks into the treeview
        for task in tasks:
            task_tree.insert("", "end", values=(task["task_name"], task["start_time"], task["end_time"], task["priority"]))

    except Exception as e:
        logging.error(f"Error viewing priority tasks: {e}")
        messagebox.showerror("Error", f"Failed to view priority tasks: {e}")
        return False

# GUI setup
root = tk.Tk()
root.title(APP_TITLE)
root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
root.configure(bg=BG_COLOR)

# Style configuration
style = ttk.Style()
style.configure("TNotebook.Tab", background=ACCENT_COLOR, foreground=FG_COLOR, font=TEXT_FONT)
style.configure("TFrame", background=BG_COLOR, foreground=FG_COLOR, font=TEXT_FONT)
style.configure("TButton", background=BUTTON_COLOR, foreground=BUTTON_TEXT_COLOR, padding=10, font=TEXT_FONT)
style.configure("TLabel", background=BG_COLOR, foreground=FG_COLOR, padding=5, font=TEXT_FONT)
style.configure("TEntry", padding=5, foreground=ENTRY_FG_COLOR, background=ACCENT_COLOR, font=TEXT_FONT)  # Darker entry background with maroon text
style.configure("Treeview", background=BG_COLOR, foreground=FG_COLOR, font=TEXT_FONT)
style.configure("Treeview.Heading", background=ACCENT_COLOR, foreground=FG_COLOR, font=TEXT_FONT)

# Notebook (Tabbed interface)
notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True, padx=10, pady=10)

# Frames (Pages)
patient_frame = ttk.Frame(notebook)
task_frame = ttk.Frame(notebook)

notebook.add(patient_frame, text="Patient Info")
notebook.add(task_frame, text="Task Info")

# --- Patient Info Frame ---
patient_id_label = ttk.Label(patient_frame, text="Patient ID (Integer):")
patient_id_label.pack(pady=(10, 2))

patient_id_No_entry = ttk.Entry(patient_frame, font=TEXT_FONT)
patient_id_No_entry.pack(pady=5)

patient_name_label = ttk.Label(patient_frame, text="Patient Name:")
patient_name_label.pack(pady=5)

patient_name_entry = ttk.Entry(patient_frame, font=TEXT_FONT)
patient_name_entry.pack(pady=5)

email_label = ttk.Label(patient_frame, text="Email Address:")
email_label.pack(pady=5)

email_entry = ttk.Entry(patient_frame, font=TEXT_FONT)
email_entry.pack(pady=5)

add_patient_button = ttk.Button(patient_frame, text="Add Patient", command=lambda: add_patient(patient_id_No_entry.get(), patient_name_entry.get(), email_entry.get()))
add_patient_button.pack(pady=10)

# --- Task Info Frame ---
task_name_label = ttk.Label(task_frame, text="Task Name:")
task_name_label.pack(pady=5)

task_name_entry = ttk.Entry(task_frame, font=TEXT_FONT)
task_name_entry.pack(pady=5)

start_time_label = ttk.Label(task_frame, text="Start Time (HH:MM):")
start_time_label.pack(pady=5)

start_time_entry = ttk.Entry(task_frame, font=TEXT_FONT)
start_time_entry.pack(pady=5)

end_time_label = ttk.Label(task_frame, text="End Time (HH:MM):")
end_time_label.pack(pady=5)

end_time_entry = ttk.Entry(task_frame, font=TEXT_FONT)
end_time_entry.pack(pady=5)

priority_label = ttk.Label(task_frame, text="Priority (1-5):")
priority_label.pack(pady=5)

priority_entry = ttk.Entry(task_frame, font=TEXT_FONT)
priority_entry.pack(pady=5)

repeat_interval_label = ttk.Label(task_frame, text="Repeat Interval:")
repeat_interval_label.pack(pady=5)

repeat_interval_entry = ttk.Entry(task_frame, font=TEXT_FONT)
repeat_interval_entry.pack(pady=5)

add_task_button = ttk.Button(task_frame, text="Add Task", command=lambda: add_task(patient_id_No_entry.get(), task_name_entry.get(), start_time_entry.get(), end_time_entry.get(), priority_entry.get(), repeat_interval_entry.get()))
add_task_button.pack(pady=10)

send_reminder_button = ttk.Button(task_frame, text="Send Reminder Email", command=lambda: send_reminder_email(patient_id_No_entry.get(), task_name_entry.get(), start_time_entry.get()))
send_reminder_button.pack(pady=10)

# View Priority Tasks Button
view_priority_tasks_button = ttk.Button(task_frame, text="View Priority Tasks", command=view_priority_tasks)
view_priority_tasks_button.pack(pady=10)

# MongoDB connection
connect_to_mongodb()

# Start GUI event loop
root.mainloop()
