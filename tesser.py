import os 
from tesserocr import PyTessBaseAPI, Image
import time
import PIL.Image
import shutil
import re

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account

SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = 'service_account.json'  
PARENT_FOLDER_ID = "1Zb05IVT8lioNx5B2m3pzi7wjXHYCkaC5" # Google Drive folder ID
creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES) # This will get the Google Drive credentials
service = build('drive', 'v3', credentials=creds)

def create_google_drive_folder(folder_name):

    file_metadata = {
        'name': folder_name,  
        'mimeType': 'application/vnd.google-apps.folder'
    }

    folder = service.files().create(body=file_metadata, fields='id').execute()
    print(f"Folder '{folder_name}' created with ID: {folder['id']}")
    return folder['id']  # Return the folder ID

def upload_file_to_drive_folder(file_path, folder_id, name):

    file_metadata = {
        'name': name,  # File name to upload
        'parents': [folder_id]  # Folder ID where the file should go
    }

    media = MediaFileUpload(file_path, mimetype='application/octet-stream') 

    # Upload the file
    file = service.files().create(
        body=file_metadata,
        media_body=media
    ).execute()

    print(f"File '{file['name']}' uploaded successfully to folder with ID: {folder_id}")

files_process = 0

tessdata_dir = 'C:/Program Files/Tesseract-OCR/tessdata'  # Replace with your tessdata path
start_time = time.time()

keywords ={
    "abstract of judgment",
    "affidavit of death of trustee",
    "release of federal tax lien",
    "federal tax lien"
    "grant deed",
    "mechanics lien",
    "notice of default",
    "notice of rescission of notice of default"
    "notice of trustee's sale",
    "quitclaim deed",
    "revocable transfer on death",
    "state franchise tax lien",
    "trustee's deed upon sale",
}

non_keywords = [
    "affidavit of death of trustee",
    "notice of rescission of notice of default",
    "release of federal tax lien",
]

def check_folder_exist(service, parent_folder_id, folder_name):
    """
    Check if a folder exists within a specific parent folder in Google Drive.
    
    :param service: Authenticated Google Drive service object
    :param parent_folder_id: ID of the parent folder to search in
    :param folder_name: Name of the folder to search for
    :return: Folder ID if exists, None otherwise
    """
    try:
        # Construct the query to find folders with the given name in the specified parent folder
        final_folders = []
        query = (f"mimeType='application/vnd.google-apps.folder' "
                 f"and name='{folder_name}' "
                 f"and '{parent_folder_id}' in parents")
        
        # Execute the search
        # First check
        results = service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name)',
            pageSize=1
        ).execute()
        
        initial_folders = results.get('files', [])
        print(f"Initial check for '{folder_name}': {len(initial_folders)} folders found")
        
        # If no folders found, wait and recheck
        if not initial_folders:
            time.sleep(8)
            
            results = service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)',
                pageSize=1
            ).execute()
            
            final_folders = results.get('files', [])
            print(final_folders)
            print(f"After waiting - check for '{folder_name}': {len(final_folders)} folders found")
            if initial_folders > final_folders:
                final_folders = initial_folders
        # print("THIS IS THE QUERY", query)
        # print("THIS IS THE RESULTS", results)
        # Get the files (folders) from the results
        print("THESE ARE THE FOLDERS", initial_folders)

        # Return the first matching folder's ID, or None if no folder found
        if initial_folders:
            return initial_folders[0]['id']
        elif final_folders:
            return final_folders[0]['id']
        else:
            return None
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    
def check_file_exists(service, folder_id, file_name):
    """
    Check if a file exists in a specific Google Drive folder.
    
    :param service: Authenticated Google Drive service object
    :param folder_id: ID of the folder to search in
    :param file_name: Name of the file to search for
    :return: File ID if exists, None otherwise
    """
    try:
        # Construct the query to find files with the given name in the specified folder
        query = (f"name='{file_name}' "
                 f"and '{folder_id}' in parents")
        
        # Execute the search
        results = service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name)'
        ).execute()
        

        # Get the files from the results
        files = results.get('files', [])
        
        # Return the first matching file's ID, or None if no file found
        return files[0]['id'] if files else None
    
    except Exception as e:
        print(f"An error occurred while checking file existence: {e}")
        return None

def check_folder_exists(folder_name):
    folder_path = f'./CREATED_FOLDERS/{folder_name}'
    isFolder = os.path.isdir(folder_path)
    if isFolder:
        return True
    else:
        return False
    
def check_file_exists(file_name, folder_name):
    file_path = f'./CREATED_FOLDERS/{folder_name}/{file_name}'
    isFile = os.path.isfile(file_path)
    if isFile:
        return True
    else:
        return False

def upload_file_to_folder(source_file_path, folder_name):
    try:
        destination_file_path = f'./CREATED_FOLDERS/{folder_name}'
        destination_file = os.path.join(destination_file_path, os.path.basename(source_file_path))
        shutil.copy(source_file_path, destination_file)
        print('File uploaded successfully to: ', folder_name)
    except:
        print('Could not upload file to folder: ',folder_name)

def search_page(page_text, page_number, file_name, file_path):
    folder_name = ''
    
    page_text = page_text.lower()
    for keyword in keywords:
        if keyword in page_text:

            if keyword in non_keywords:
                print(f"KEYWORD '{keyword}' is in the non_keywords list. Skipping upload...")
                return 
            
            if len(keyword) > len(folder_name):
                folder_name = keyword

            print(f"FOUND '{folder_name}' on page {page_number} in {file_name}")

            isFolder = check_folder_exists(folder_name)
            
            if isFolder:

                print(f"DIRECTORY ALREADY EXISTS: {folder_name}")
                
                # Check if file already exists in the folder
                isFile = check_file_exists(file_name, folder_name)
                
                if isFile:
                    print(f"File {file_name} already exists in the folder")
                else:
                    # Upload file if it doesn't exist
                    upload_file_to_folder(file_path, folder_name)
            else:
                os.mkdir(f'./CREATED_FOLDERS/{folder_name}')
                upload_file_to_folder(file_path, folder_name)
    
            break
            
def readfolder(base_folder):
    target_folder_name = "SET1"
    
    # Construct base directory path
    base_directory = f"./extracted_folders/{base_folder}"
    target_directory_path = None

    # Ensure the base directory exists
    if not os.path.exists(base_directory):
        print(f"Base directory '{base_directory}' does not exist.")
        return {
            "status": "error",
            "message": f"Base directory '{base_directory}' does not exist."
        }

    # Traverse through the directory tree
    for root, dirs, _ in os.walk(base_directory):
        if target_folder_name in dirs:
            target_directory_path = os.path.join(root, target_folder_name)
            print(f"Target folder found: {target_directory_path}")
            return  target_directory_path
        
# Process each TIFF file in the directory
with PyTessBaseAPI(path=tessdata_dir) as api:
    directory_path = readfolder('20241125-Redacted-Drawoff')
    for file_name in os.listdir(directory_path):
        if file_name.endswith('.tif'):  # Process only TIFF files
            file_path = os.path.join(directory_path, file_name)
            print(f"Processing file: {file_name}")
            files_process += 1

            # Open the TIFF file using PIL
            pil_image = PIL.Image.open(file_path)
            
            # Get the number of pages
            n_pages = pil_image.n_frames
            
            # Initialize page_text as an empty string
            page_text = ""

            # Check if there's a second page (page index 1)
            if n_pages >= 2:
                # Go to the second page (index 1)
                pil_image.seek(1)
                
                # Convert PIL Image to Tesseract Image
                api.SetImage(pil_image)
                
                # Extract text from page 2
                page_text = api.GetUTF8Text()
                print("Extracted text from Page 2:")
                page_number = 2
            
            # If no second page, fall back to first page (index 0)
            elif n_pages >= 1:
                # Go to the first page (index 0)
                pil_image.seek(0)
                
                # Convert PIL Image to Tesseract Image
                api.SetImage(pil_image)
                
                # Extract text from page 1
                page_text = api.GetUTF8Text()
                print("Extracted text from Page 1 (no second page found):")
                page_number = 1
            
            # If no pages found
            else:
                print(f"No pages found in the file: {file_name}")
                continue

            # Print a snippet of the extracted text
            
            # Search for keywords in the extracted page
            search_page(page_text, page_number, file_name, file_path)
            
            print("total time: ", time.time() - start_time)
            print("files processed: ", files_process)
            print("files per second:", files_process / (time.time() - start_time))
            print("-" * 50)

            
