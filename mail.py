from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request as GoogleAuthRequest
from googleapiclient.discovery import build
import os, pickle, secrets, base64, hashlib
from flask.json import jsonify

import pickle
import os
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText



SCOPES = ['https://www.googleapis.com/auth/gmail.send']

'''The pieces of this code are referenced
   from the official Google Gmail API do-
   cumentation. Find the link below! 
'''

'''https://developers.google.com/gmail/api/quickstart/python'''

def credentials():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(GoogleAuthRequest())
        else:
            path_to_cred_file = 'client_secret.json'
            flow = InstalledAppFlow.from_client_secrets_file(path_to_cred_file, SCOPES)
            creds = flow.run_local_server()
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return creds

def builder():
    creds = credentials()
    service = build('gmail', 'v1', credentials=creds)
    return service

def sender(email):
    service = builder()
    email_content = MIMEMultipart()
    email_content["From"] = "312isthecharm@gmail.com"
    email_content["To"] = email
    email_content["Subject"] = "Verify your email"

    t0ken = secrets.token_bytes(80)

    encoded_t0ken = base64.urlsafe_b64encode(t0ken).decode('utf-8')

    hashed_token = hashlib.sha256(encoded_t0ken.encode()).hexdigest()

    link = f"http://localhost:8080/blankVerify.html?email={email}&token={hashed_token}"

    description = f"Please confirm your email address by clicking the link below!\r\n{link}\r\n\r\n~Second time's the charm"

        
    email_content.attach(MIMEText(description, 'plain'))
    encoded_message = base64.urlsafe_b64encode(email_content.as_string().encode()).decode()
    encoded_email_content = {'raw': encoded_message}
    service.users().messages().send(userId="me", body=encoded_email_content).execute()