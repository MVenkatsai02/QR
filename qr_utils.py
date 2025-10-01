import qrcode
import hashlib
import os
from datetime import datetime

QR_FOLDER = "qrcodes"

def generate_daily_qr(office_id="OFFICE-001"):
    today = datetime.utcnow().strftime("%Y-%m-%d")
    raw_token = f"{office_id}-{today}-secret"
    token = hashlib.sha256(raw_token.encode()).hexdigest()

    if not os.path.exists(QR_FOLDER):
        os.makedirs(QR_FOLDER)

    img = qrcode.make(token)
    img_path = os.path.join(QR_FOLDER, f"qr_{today}.png")
    img.save(img_path)

    return token, today, img_path
