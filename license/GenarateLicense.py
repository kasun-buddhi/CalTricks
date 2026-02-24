import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from License import License
from LicenseConfig import *

BASE_DIR         = os.path.dirname(os.path.abspath(__file__))
csv_path         = os.path.join(BASE_DIR,CSV_FILE_PATH )
lic              = License(
user_email       = "set_email",
product_code     = "CALTRICKS",
expiry_date      = "2027-02-27",
csv_file         = csv_path)
key              = lic.generate_license()
lic.save_to_csv()
print("License Key:")
print(key)