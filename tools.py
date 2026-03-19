###############################
##  TOOLS
from langchain.agents import Tool
from langchain.tools import BaseTool
from langchain.tools import StructuredTool
import streamlit as st
from datetime import date
from dotenv import load_dotenv
import json
import re
import os
import imaplib
import email
import sys
import smtplib
from email.message import EmailMessage

HOST = 'host.docker.internal'
PORT = 1143
SMPT_PORT = 2525
FROM_EMAIL = "bot@bot.com"

USERNAME = 'a'  # fill in your username
PASSWORD = 'a'  # fill in your password

    
def send_email(json_input : str):
    """Sends an email. Input to this tool must be a SINGLE JSON STRING with to_email, subject, body attributes."""
    try:
        # Parse the JSON string
        print(json_input)
        data = json.loads(json_input.replace("\n","\\n"))
        subject = data['subject']
        body = data['body']
        to_email = data['to_email']# Usage

        # Create email message
        msg = EmailMessage()
        msg.set_content(body)
        msg['Subject'] = subject
        msg['From'] = FROM_EMAIL
        msg['To'] = to_email

        # Connect to SMTP server and send email
        with smtplib.SMTP(HOST, SMPT_PORT) as server:
            server.login(FROM_EMAIL, PASSWORD)
            server.send_message(msg)
    except Exception as e:
        return f"Error: {e}"

def get_first_text_part(msg):
    """Extract the first text/plain part of a MIME email message."""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == 'text/plain':
                return part.get_payload(decode=True)
    else:
        return msg.get_payload(decode=True)
load_dotenv()

def get_user_emails(input : str):

    messages = ""
    try:
        # Connect to the IMAP server
        mail = imaplib.IMAP4(HOST, PORT)

        # Login to the server
        mail.login(USERNAME, PASSWORD)

        # Select the INBOX
        typ, data = mail.select('INBOX', readonly=True)
        if typ != 'OK':
            print("Error selecting INBOX.")
            sys.exit()

        # Get the total number of emails in the inbox
        num_messages = int(data[0])
        start = max(1, num_messages - 9)  # Fetch the last 10 or fewer emails

        for i in range(start, num_messages + 1):
            typ, msg_data = mail.fetch(str(i), '(RFC822)')
            if typ != 'OK':
                print(f"Error fetching message {i}: {typ}")
                continue

            msg = email.message_from_bytes(msg_data[0][1])
            sender = msg['From']
            subject = msg['Subject']
            body = get_first_text_part(msg)

            messages += f"Message {i}:"
            messages += f"From: {sender}"
            messages += f"Subject: {subject}"
            messages += f"Body:\n{body.decode('utf-8', 'ignore')}\n"

        # Logout from the server
        mail.logout()

        return messages
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

get_user_emails_tool = Tool(
    name='GetUserEmails',
    func= get_user_emails,
    description="Returns a list of the emails in the user's inbox."
)

send_emails_tool = StructuredTool.from_function(send_email) 

Tool(
    name='SendEmail',
    func= send_email,
    description="Sends an email. Input to this tool must be a SINGLE JSON STRING with to_email, subject, body attributes."
)