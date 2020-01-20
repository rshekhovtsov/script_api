import pickle
import os.path
import socket
import json

from datetime import datetime
from googleapiclient import errors
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

socket.setdefaulttimeout(120)

SCOPES = ['https://www.googleapis.com/auth/forms',
          'https://www.googleapis.com/auth/script.send_mail',
          'https://www.googleapis.com/auth/script.projects']

MANIFEST = '''
{
    "timeZone": "America/New_York",
    "exceptionLogging": "STACKDRIVER",
    "executionApi": {
        "access": "ANYONE"
    }
}
'''.strip()

SCRIPT_ID = 'qwertyuiopQWERTYUIOPasdfghjkl123456789zxcvbnmASDFGHJKL54'


def login():
    creds = None
    cred_path = '../.credentials/'
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                cred_path + 'google_test_project.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('script', 'v1', credentials=creds)
    return service


def update_project(service):
    # Read from file code we want to deploy
    with open('export-google-form.gs', 'r') as f:
        sample_code = f.read()

    # Upload two files to the project
    request = {
        'files': [{
            'name': 'hello',
            'type': 'SERVER_JS',
            'source': sample_code
        }, {
            'name': 'appsscript',
            'type': 'JSON',
            'source': MANIFEST
        }
        ]
    }

    # Update files in the project
    service.projects().updateContent(
        body=request,
        scriptId=SCRIPT_ID
    ).execute()


# Get JSON, which is returned by script
def get_json(service):
    body = {
        "function": "main",
        "devMode": True
    }
    # Get JSON from script
    resp = service.scripts().run(scriptId=SCRIPT_ID, body=body).execute()

    # Write out JSON to file
    scenario_dir = './'
    with open(scenario_dir + 'habr_auto.json', 'w') as f:
        json.dump(resp['response']['result'], f, ensure_ascii=False, indent=4)

def main():
    try:
        service = login()
        update_project(service)
        get_json(service)

    except errors.HttpError as error:
        # The API encountered a problem.
        print(error.content.decode('utf-8'))


if __name__ == '__main__':
    main()
