from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
import os
import shutil
from Config import *


class DriveDataBase:
    def __init__(self,folder):
        self.token_path     = TOKEN_PATH
        self.scopes         = DRIVE_SCOPES
        self.service        = None
        self.folder         = folder
    
    def _authenticate(self):
        # Check if env variable is set
        if not self.token_path:
            raise ValueError("Token path not set.")
        # Ensure directory exists
        token_dir    = os.path.dirname(self.token_path)
        if token_dir and not os.path.exists(token_dir):
            os.makedirs(token_dir)
        creds        = None
        # If token file exists, load it
        if os.path.exists(self.token_path):
            creds    = Credentials.from_authorized_user_file(self.token_path, self.scopes)
        # If no valid creds, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow     = InstalledAppFlow.from_client_secrets_file('credentials.json', self.scopes)
                creds    = flow.run_local_server(port=0)
            with open(self.token_path, 'w') as f:
                f.write(creds.to_json())
        return creds
    
    def _check_exists(self, name, parent_id, is_folder = False):
        """Check if a file or folder already exists in Google Drive"""
        try:
            # Build the query
            query = f"name='{name}' and '{parent_id}' in parents and trashed = false"
            # Add MIME type filter for folders only  ##Multipurpose Internet Mail Extensions
            if is_folder:
                query       +=  " and mimeType='application/vnd.google-apps.folder'"
            results          =  self.service.files().list(
                q            =  query,
                fields       = 'files(id, name)',
                pageSize     =  1).execute()
            files            =  results.get('files', [])
            if files:
                return files[0].get('id')
            return None
        except HttpError as e :
            print(f"HTTP Error : {name} - {e} ")
        except Exception as e :
            print(f"Error checking files: {e}")
        
    def _create_folder(self, folder_name, parent_id):
        """Create a folder in Google Drive (or return existing)"""
        try:
            # Check if folder already exists
            existing_id      =  self._check_exists(folder_name, parent_id, is_folder=True)
            if existing_id:
                print(f"Folder already exists: {folder_name} (ID: {existing_id})")
                return existing_id
            file_metadata    = {
            'name'          : folder_name,
            'mimeType'      : 'application/vnd.google-apps.folder',
            'parents'       : [parent_id]}
            folder           = self.service.files().create(
            body             = file_metadata,
            fields           = 'id, name').execute()
            print(f"Created folder: {folder_name} (ID: {folder.get('id')})")
            return folder.get('id')
        except HttpError as e :
            print(f" HTTP Error Creating Folders : {folder_name} : {e}")
        except Exception as e : 
            print(f"Error Creating folder : {folder_name} : {e}")   
    
    def _upload_file(self, file_path, parent_id):
        """Upload a single file to Google Drive (skip if exists)"""
        try:
            file_name        = os.path.basename(file_path)
            # Check if file already exists
            existing_id      = self._check_exists(file_name, parent_id, is_folder=False)
            if existing_id:
                print(f"File already exists, skipping: {file_name}")
                return None
            file_metadata   = {
            'name'          : file_name,
            'parents'       : [parent_id]}
            media           = MediaFileUpload(file_path, resumable=True)
            print(f"Uploading: {file_name}...")
            uploaded_file   = self.service.files().create(
            body            = file_metadata,
            media_body      = media,
            fields          = 'id, name, webViewLink').execute()
            filename        = uploaded_file.get('name')
            print(f"Uploaded: {filename}")
            return uploaded_file, filename
        except HttpError as e :
            if e.resp.status == 403 :
                if "storageQuotaExceeded" in str(e):
                    print(f"Storage Almost full")
                    print(f"Cannot upload : {file_name}")
                    raise Exception("Storage quota exceeded - upload stopped") from e
                else:
                    print(f"Permission error uploading : {file_name} : {e}")
            elif e.resp.status == 404 :
                print(f"file not found : {file_name: {e}}")
            elif e.resp.status == 400 :
                print(f" Invalid request for {file_name} : {e}")
            else : 
                print(f"HTTP Error {e.resp.status}  uploading : {file_name} : {e}")
            return None
        except Exception as e :
            print(f" Unexpected error uploading : {file_name} : {e}")
            return None
    
    def _upload_folder(self, local_path, parent_id):
        """Recursively upload folder structure to Google Drive"""
        try:
           # Get all items in the current directory
            items           = os.listdir(local_path)
            for item in items:
                item_path   = os.path.join(local_path, item)
                if os.path.isdir(item_path):
                    # It's a folder - create it in Drive and recurse
                    print(f"Processing folder: {item}")
                    folder_id = self._create_folder(item, parent_id)
                    # Recursively upload contents of this folder ( sub foders)
                    self._upload_folder(item_path, folder_id)
                elif os.path.isfile(item_path):
                    # It's a file - upload it
                    files = self._upload_file(item_path, parent_id)
            return item
        except  Exception as e :
            print(f" Error in Folder upload : {e}")
            
    def upload_asset_folder(self):
        """Upload entire Asset folder structure to Google Drive"""
        try:
            creds            = self._authenticate()
            self.service     = build("drive", "v3", credentials=creds)
            print(f"Starting upload of: {self.folder}")
            if not os.path.exists(self.folder):
                print(f"Error: {self.folder} does not exist!")
                return
            # Create main "Asset" folder in Google Drive (or use existing)
            main_folder_name        = os.path.basename(self.folder)
            main_folder_id         = self._create_folder(main_folder_name, GOOGLE_DRIVE_PARENT_FOLDER_ID)
            # Upload all contents recursively
            filename = self._upload_folder(self.folder, main_folder_id)
            print("Upload completed successfully!")
            return filename 
        except Exception as e :
            print(f"upload failed : {e}")
            return None