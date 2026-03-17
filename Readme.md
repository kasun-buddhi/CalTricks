# CALTRICKS

##  Introduction
Caltrick is an automation tool that scrapes assets from the Craftnest website, downloads them and uploads them to Google Drive.  

## System Overview
The **CALTRICKS** project is a well-structured Python application built using Playwright,Python.  
It consists of two main folders:  

- **data_scraper**  - Handles data scraping from Craftnest.  
- **drive**         - Contains core utilities and reusable components.   

---
## Note

### Prerequisites 

## 1. Install Python 3.12.3(Windows)

- Step 1 : Download Python
         Go to  https://www.python.org/downloads/release/python-3123/

- Step 2: Run the installer.
- Step 3: Verify installation

```bash
python --version

```
## 2. Install Pip 
- Step 1: Download get-pip.py
        Go to: https://bootstrap.pypa.io/get-pip.py
- Step 2: Install pip 24.0
- Step 3: Verify installation
```bash
pip --version

```
--- 
        
1.The ``requirements.txt`` file should list all Python libraries that need to be installed using:
```bash
pip install -r requirements.txt
```
2.Create service account ``JSON (for Google Drive Upload)``
```bash
#--Step 01
Visit: https://console.cloud.google.com
#--Step 02
Create a New Project
#--Step 03
Enable Google Drive API
#--Step 04
Create a Service Account
#--Step 05
Create a JSON Key
```
1.1 . Install Playwright new browsers
``` bash
playwright install
```
3.Setup Environment variables 
 ### Linux/macOs
 ```bash
 #--Step 01
  nano ~/.bashrc

 #--Step 02
  export CRAFTNEST_USERNAME   ="craftnest_username"
  export CRAFTNEST_PASSWORD   ="craftnest_password"
  export TOKEN_PATH           ="path/token.json"
 ```
Save variables.

### Windows
```bash
#--Step 01
Open Environment Variables Panel
Press Win + S and search for: “Edit the system environment variables”
Click the button labeled “Environment Variables…”
#--Step 02
Add New Variables
Under User variables (for current user) or System variables (for all users),
click New…

Add:
Variable name   : CRAFTNEST_USERNAME
Variable value  : "craftnest_usernam"

Repeat for:
Variable name   : CRAFTNEST_PASSWORD
Variable value  : "craftnest_password"

Repeat for:
Variable name   : TOKEN_PATH 
Variable value  : path/token.json

#--Step03
Click OK to save and close all dialogs.
```


## Main Class

### How to Run

- Navigate to the Project Folder.

- Run the main.py file using the following command:
```bash
   python main.py
```

## Data Scraper
The ```data_scraper``` module forms the core of the project’s scraping and asset‑processing. It handles critical tasks such as extracting categories, sub‑categories, and asset links from the CraftNest website, as well as managing automated downloads.  
It contains the main script:
```
-  CraftNest.py
-  SubCategory.py 
-  Asset.py 
-  DownloadAsset.py 
```

### CraftNest Class
This class initializes the Playwright browser, handles secure web authentication, and performs structured scraping of all primary categories from the CraftNest website.

### SubCategory Class
This class is responsible for scraping all sub‑categories associated with each primary category returned by the ``CraftNest`` class It processes category-level URLs, navigates through each section.

### Asset  Class
This class is responsible for scraping all asset_links associated with each sub category returned by the``SubCategory`` class.

### DownloadAsset Class
This class is responsible for downloading all asset links associated with each sub‑category returned by the ``Asset`` class. It handles navigation to each asset page, triggers secure file downloads, and manages the local storage of downloaded resources in a structured directory format.

## Drive
The ``drive`` module manages the upload of assets to Google Drive using a well‑structured and organized folder format. It handles authentication through a service account or OAuth credentials and provides a reliable interface for creating folders, uploading files.
It contains the main script:
```
- DriveDataBase.py
```

### DriveDataBase Class
this class initializes the google drive , handles create structured file folders and upload asset.