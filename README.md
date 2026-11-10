# FeedbackTrack

A Python tkinter desktop application for submitting and tracking feedback, with user and admin accounts. It uses Firebase (Authentication and Firestore) as its backend.

## Requirements
- Python 3.8 or newer (tkinter is included with the standard Python installer)
- An internet connection
- The `requests` library

## Setup and run
1. Download or clone this repository.
2. Install the dependency:
   pip install requests
3. Start the app from the project folder:
   python main.py

## Features
- Sign up and log in (user and admin accounts)
- Submit feedback
- View and track your feedback
- Admins can manage feedback status and reply in conversations

## Files
- `main.py` - entry point, opens the landing page
- `firebase_config.py` - Firebase connection (uses only a public web API key)
- other `.py` files - individual screens of the application