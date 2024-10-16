#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import subprocess
import signal

ngrok_process = None  # Global variable to store the ngrok process

def start_ngrok():
    """Function to start ngrok"""
    try:
        print("Starting ngrok...")
        # Start ngrok on port 8000
        global ngrok_process
        ngrok_process = subprocess.Popen(["ngrok", "http", "8000", "--domain=profound-moccasin-composed.ngrok-free.app"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        print("ngrok not found. Make sure it is installed and in your PATH.")

def stop_ngrok():
    """Function to stop ngrok when shutting down the Django server"""
    global ngrok_process
    if ngrok_process:
        print("Stopping ngrok...")
        ngrok_process.terminate()  # Gracefully terminate the process
        ngrok_process.wait()       # Wait for ngrok to shut down

def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'runserver':
        start_ngrok()
        
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eco_sys.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    try:
        execute_from_command_line(sys.argv)
    finally:
        # This block is executed when Django server shuts down
        stop_ngrok()


if __name__ == '__main__':
    main()
