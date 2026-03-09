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
    def __init__(self, folder):
        self.token_path = TOKEN_PATH
        self.scopes     = DRIVE_SCOPES
        self.service    = None
        self.folder     = folder  


    def _authenticate(self):
        if not self.token_path:
            raise ValueError("Token path not set.")
        token_dir = os.path.dirname(self.token_path)
        if token_dir and not os.path.exists(token_dir):
            os.makedirs(token_dir)
        creds = None
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, self.scopes)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"Token refresh failed: {e}")
                    print("Deleting expired token and re-authenticating...")
                    os.remove(self.token_path)
                    creds = None
            if not creds:
                flow  = InstalledAppFlow.from_client_secrets_file('credentials.json', self.scopes)
                creds = flow.run_local_server(port=0)
            with open(self.token_path, 'w') as f:
                f.write(creds.to_json())
        return creds


    def _escape_query(self, name):
        """
        Escape single quotes in filenames for Google Drive API query.
        Example: "St Patrick's Day.zip" -> "St Patrick\\'s Day.zip"
        """
        return name.replace("\\", "\\\\").replace("'", "\\'")


    def _check_exists(self, name, parent_id, is_folder=False):
        """Check if a file or folder already exists in Google Drive."""
        try:
            safe_name = self._escape_query(name)
            query     = f"name='{safe_name}' and '{parent_id}' in parents and trashed = false"
            if is_folder:
                query += " and mimeType='application/vnd.google-apps.folder'"
            results = self.service.files().list(
                q        = query,
                fields   = 'files(id, name)',
                pageSize = 1
            ).execute()
            files = results.get('files', [])
            return files[0].get('id') if files else None
        except HttpError as e:
            print(f"HTTP Error checking: {name} - {e}")
        except Exception as e:
            print(f"Error checking files: {e}")


    def _get_or_create_folder(self, folder_name, parent_id):
        """Get existing folder on Drive or create it if it doesn't exist."""
        try:
            existing_id = self._check_exists(folder_name, parent_id, is_folder=True)
            if existing_id:
                return existing_id
            file_metadata = {
                'name'    : folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents' : [parent_id]
            }
            folder = self.service.files().create(
                body   = file_metadata,
                fields = 'id, name'
            ).execute()
            print(f"Created folder: {folder_name} (ID: {folder.get('id')})")
            return folder.get('id')
        except HttpError as e:
            print(f"HTTP Error creating folder: {folder_name} : {e}")
        except Exception as e:
            print(f"Error creating folder: {folder_name} : {e}")


    def _upload_file(self, file_path, parent_id):
        """Upload a single file to Google Drive (skip if exists)."""
        file_name = os.path.basename(file_path)
        try:
            existing_id = self._check_exists(file_name, parent_id, is_folder=False)
            if existing_id:
                print(f"  Already exists, skipping: {file_name}")
                return None
            file_metadata = {
                'name'   : file_name,
                'parents': [parent_id]
            }
            media = MediaFileUpload(file_path, resumable=True)
            print(f"  Uploading: {file_name}...")
            uploaded_file = self.service.files().create(
                body       = file_metadata,
                media_body = media,
                fields     = 'id, name'
            ).execute()
            print(f"  Uploaded : {uploaded_file.get('name')}")
            return uploaded_file
        except HttpError as e:
            if e.resp.status == 403 and "storageQuotaExceeded" in str(e):
                print(f"Storage full. Cannot upload: {file_name}")
                raise Exception("Storage quota exceeded - upload stopped") from e
            print(f"HTTP Error {e.resp.status} uploading: {file_name} : {e}")
            return None
        except Exception as e:
            print(f"Unexpected error uploading: {file_name} : {e}")
            return None


    def _upload_folder_recursive(self, local_path, parent_id):
        """
        Recursively upload a local folder to Google Drive,
        mirroring the exact folder structure.
        Structure mirrored:
          Asset/
            cliparts/
              alphabet_clipart/
                01_I Floral Alphabet Clipart Bundle/
                  03069_I Floral Alphabet Clipart Bundle.zip
                  thumbnail.jpeg
                  data.json
                  images/
                    sample_01.jpeg
                    sample_02.jpeg
        """
        uploaded_count = 0
        try:
            for item in sorted(os.listdir(local_path)):
                item_path = os.path.join(local_path, item)
                if os.path.isdir(item_path):
                    print(f"\Folder: {item}")
                    folder_id       = self._get_or_create_folder(item, parent_id)
                    if folder_id:
                        uploaded_count += self._upload_folder_recursive(item_path, folder_id)
                elif os.path.isfile(item_path):
                    result = self._upload_file(item_path, parent_id)
                    if result:
                        uploaded_count += 1
        except Exception as e:
            print(f"Error in recursive upload: {e}")
        return uploaded_count


    def upload_asset_folder(self):
        """
        Upload entire local Asset folder to Google Drive,
        using GOOGLE_DRIVE_PARENT_FOLDER_ID as the root.
        Local structure:
          DOWNLOAD_ASSET_LOCATION/
            Asset/
              cliparts/
                alphabet_clipart/
                  01_Name/
                    file.zip
                    thumbnail.jpeg
                    data.json
                    images/
        Drive structure (mirrors exactly):
          GOOGLE_DRIVE_PARENT_FOLDER_ID/
            Asset/
              cliparts/
                alphabet_clipart/
                  01_Name/
                    file.zip
                    thumbnail.jpeg
                    data.json
                    images/
        """
        try:
            creds        = self._authenticate()
            self.service = build("drive", "v3", credentials=creds)
            if not os.path.exists(self.folder):
                print(f"[Upload] Error: local folder does not exist: {self.folder}")
                return
            print(f"[Upload] Starting upload: {self.folder}")
            print(f"[Upload] Drive root ID  : {GOOGLE_DRIVE_PARENT_FOLDER_ID}\n")
            # Get or create top-level Asset folder on Drive
            root_folder_name     = os.path.basename(self.folder)  # "Asset"
            root_folder_id       = self._get_or_create_folder(root_folder_name, GOOGLE_DRIVE_PARENT_FOLDER_ID)
            total_uploaded       = self._upload_folder_recursive(self.folder, root_folder_id)
            print(f"\n[Upload] Done! Total files uploaded: {total_uploaded}")
            return total_uploaded
        except Exception as e:
            print(f"[Upload] Failed: {e}")
            return None


    def find_asset_folder_by_name(self, folder_name, sub_category_path):
        """
        Find an existing asset folder on Drive by folder name within sub_category path.
        Example:
            folder_name       : 01_I Floral Alphabet Clipart Bundle
            sub_category_path : Asset/cliparts/alphabet_clipart
        Returns: Drive folder ID or None
        """
        try:
            # Navigate to sub_category folder
            parts     = sub_category_path.split("/")
            folder_id = GOOGLE_DRIVE_PARENT_FOLDER_ID
            for part in parts:
                folder_id = self._check_exists(part, folder_id, is_folder=True)
                if not folder_id:
                    print(f"  [Drive] Path not found: {part}")
                    return None
            # Search for asset folder by name inside sub_category
            asset_folder_id = self._check_exists(folder_name, folder_id, is_folder=True)
            if asset_folder_id:
                print(f"  [Drive] Found folder: '{folder_name}'")
            else:
                print(f"  [Drive] Folder not found: '{folder_name}'")
            return asset_folder_id
        except Exception as e:
            print(f"  [Drive] Error finding folder: {e}")
            return None


    def find_asset_folder_by_zip(self, zip_filename, sub_category_path):
        """
        Search Google Drive for an existing asset folder that contains a zip
        matching the given filename, within the given sub_category path.
        Example:
            zip_filename      : 03069_I Floral Alphabet Clipart Bundle.zip
            sub_category_path : Asset/cliparts/alphabet_clipart
        Returns:
            folder_id  : Drive folder ID if found
            None       : if not found
        """
        try:
            # Navigate to sub_category folder on Drive
            parts     = sub_category_path.split("/")   # ['Asset', 'cliparts', 'alphabet_clipart']
            folder_id = GOOGLE_DRIVE_PARENT_FOLDER_ID
            for part in parts:
                folder_id = self._check_exists(part, folder_id, is_folder=True)
                if not folder_id:
                    print(f"  [Drive] Folder not found on Drive: {part}")
                    return None
            # folder_id is now the sub_category folder
            # Search inside it for asset folders that contain the zip
            safe_zip  = self._escape_query(zip_filename)
            query     = (
                f"name='{safe_zip}' "
                f"and trashed=false "
                f"and mimeType!='application/vnd.google-apps.folder'"
            )
            results   = self.service.files().list(
                q      = query,
                fields = "files(id, name, parents)",
            ).execute()
            files = results.get('files', [])
            if not files:
                print(f"  [Drive] Zip not found on Drive: {zip_filename}")
                return None
            # Return the parent folder ID of the zip file
            asset_folder_id = files[0].get('parents', [None])[0]
            print(f"  [Drive] Found existing asset folder (id={asset_folder_id})")
            return asset_folder_id
        except Exception as e:
            print(f"  [Drive] Error searching for zip: {e}")
            return None


    def upload_scrape_data(self, local_dir, drive_folder_id):
        """
        Upload only scrape data (data.json, thumbnail.jpeg, images/)
        into an existing Drive folder by ID. Skips zip files.
            local_dir       : local asset folder path
            drive_folder_id : existing Google Drive folder ID
        """
        SKIP_EXTENSIONS = {'.zip'}
        uploaded_count  = 0
        try:
            for item in sorted(os.listdir(local_dir)):
                item_path = os.path.join(local_dir, item)
                ext       = os.path.splitext(item)[1].lower()
                if os.path.isdir(item_path):
                    # e.g. images/ subfolder
                    sub_folder_id = self._get_or_create_folder(item, drive_folder_id)
                    if sub_folder_id:
                        for img in sorted(os.listdir(item_path)):
                            img_path = os.path.join(item_path, img)
                            if os.path.isfile(img_path):
                                result = self._upload_file(img_path, sub_folder_id)
                                if result:
                                    uploaded_count += 1
                elif os.path.isfile(item_path) and ext not in SKIP_EXTENSIONS:
                    result = self._upload_file(item_path, drive_folder_id)
                    if result:
                        uploaded_count += 1
            print(f"  [Drive] Uploaded {uploaded_count} file(s) to existing folder")
            return uploaded_count
        except Exception as e:
            print(f"  [Drive] Error uploading scrape data: {e}")
            return 0


    def delete_folder(self, folder_path):
        """Delete local folder after successful upload."""
        try:
            shutil.rmtree(folder_path)
            print(f"[Local] Deleted: {folder_path}")
        except FileNotFoundError:
            print(f"[Local] Folder not found: '{folder_path}'")
        except Exception as e:
            print(f"[Local] Error deleting folder: {e}")