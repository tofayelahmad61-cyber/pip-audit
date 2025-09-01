import os
import datetime
import paramiko
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle

# -----------------------------
# Google API Setup
# -----------------------------
SCOPES = ['https://www.googleapis.com/auth/drive.file','https://www.googleapis.com/auth/spreadsheets']

def google_authenticate():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=8080)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds

# -----------------------------
# MikroTik Backup (via SSH)
# -----------------------------
MT_HOST = "192.168.216.1"
MT_USER = "admin"
MT_PASS = "root"

def mikrotik_backup():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(MT_HOST, username=MT_USER, password=MT_PASS)

    backup_file = f"mikrotik_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.backup"
    command = f"/system backup save name={backup_file}"
    ssh.exec_command(command)
    ssh.close()
    return backup_file

# -----------------------------
# Upload to Google Drive
# -----------------------------
def upload_to_drive(creds, file_path):
    service = build('drive', 'v3', credentials=creds)
    file_metadata = {'name': os.path.basename(file_path), 'parents': ['1J613cJL_MJPdMC0WSVwv2MUph8humD3j']}
    media = MediaFileUpload(file_path, resumable=True)
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print("Uploaded to Drive. File ID:", file.get('id'))

# -----------------------------
# Log to Google Sheets
# -----------------------------
def log_to_sheets(creds, backup_file):
    service = build('sheets', 'v4', credentials=creds)
    sheet_id = "1nZA-NF8XGcBlKFWUnBoYugTn_MK3PWooDXNEcyD_uqM"
    values = [[str(datetime.datetime.now()), backup_file, "Uploaded"]]
    body = {'values': values}
    service.spreadsheets().values().append(
        spreadsheetId=sheet_id,
        range="Sheet1!A:C",
        valueInputOption="RAW",
        body=body
    ).execute()
    print("Logged to Google Sheets.")

if __name__ == "__main__":
    creds = google_authenticate()
    backup_file = mikrotik_backup()
    # এখানে ধরা হচ্ছে backup ফাইল লোকালি সেভ হয়েছে
    open(backup_file, "w").write("Dummy backup content")
    upload_to_drive(creds, backup_file)
    log_to_sheets(creds, backup_file)
