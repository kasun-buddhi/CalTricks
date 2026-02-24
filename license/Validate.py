import hmac
import hashlib
from datetime import datetime
from license.License import get_secret_key


class Validate:
    def __init__(self, input_key):
        self.input_key  = input_key
        self.secret_key = get_secret_key()

    def validate_license(self, input_key):
        parts           =  input_key.strip().split("|")
        if len(parts)  !=  4:
            return "Invalid Format"
        user_email, product_code, expiry_date, signature_from_user = [p.strip() for p in parts]
        base_string            = f"{user_email}|{product_code}|{expiry_date}"
        recalculated_signature = hmac.new(self.secret_key, base_string.encode(), digestmod=hashlib.sha256).hexdigest()
        if not hmac.compare_digest(recalculated_signature, signature_from_user):
            return "Invalid Signature"
        today   = datetime.today().date()
        expiry  = datetime.strptime(expiry_date, "%Y-%m-%d").date()
        if today > expiry:
            return "EXPIRED"
        return "VALID"