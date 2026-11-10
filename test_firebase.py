
print("Starting Firebase test...")

from firebase_config import db

print("Firebase connection initialized!")

task = {
    "task_name": "Test Firebase connection",
    "priority": "High",
    "completed": False
}

doc_ref = db.collection("tasks").add(task)

print("Task added successfully!")
print("Task ID:", doc_ref[1].id)