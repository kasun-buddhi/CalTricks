import hmac
import hashlib
import csv
import os
from datetime import datetime
try:
    from license.LicenseConfig import *  
except ModuleNotFoundError:
    from LicenseConfig import *  
def get_secret_key():
    p1       = "X9#kP"
    p2       = "2$mQ7"
    p3       = "@nR4!"
    p4       = "wL6&v"
    return (p1 + p2 + p3 + p4).encode()


class License:
    def __init__(self, user_email = None, product_code = None, expiry_date = None, csv_file = CSV_FILE_PATH):
        self.user_email     = user_email
        self.product_code   = product_code
        self.expiry_date    = expiry_date
        self.secret_key     = get_secret_key()
        self.license_key    = None
        self.csv_file       = csv_file

    def generate_license(self):
        base_string         = f"{self.user_email}|{self.product_code}|{self.expiry_date}"
        signature           = hmac.new(self.secret_key, base_string.encode(), digestmod=hashlib.sha256).hexdigest()
        self.license_key    = f"{self.user_email}|{self.product_code}|{self.expiry_date}|{signature}"
        return self.license_key

    def save_to_csv(self):
        if not self.license_key:
            raise ValueError("No license generated yet. Call generate_license() first.")
        file_exists = os.path.isfile(self.csv_file)
        with open(self.csv_file, mode="a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["user_email", "product_code", "expiry_date", "license_key", "generated_at"])
            if not file_exists:
                writer.writeheader()
            writer.writerow({
                "user_email"    : self.user_email,
                "product_code"  : self.product_code,
                "expiry_date"   : self.expiry_date,
                "license_key"   : self.license_key,
                "generated_at"  : datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        print(f"License saved to {self.csv_file}")