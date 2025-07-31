import os

SERVER = 'https://workable-primarily-ferret.ngrok-free.app'

MOMO_PARTNER_CODE = 'MOMO'
MOMO_ACCESS_KEY = 'F8BBA842ECF85'
MOMO_SECRET_KEY = 'K951B6PE1waDMi640xX08PD3vg6EkVlz'

# --- URL MoMo sẽ gọi về server của bạn ---
# Thay 'https://yourdomain.com' bằng tên miền thực tế của bạn khi triển khai
# IPN_URL_BASE = 'https://yourdomain.com/momo/ipn-handler'
MOMO_IPN_URL_BASE = f'{SERVER}/momo/confirm-payment'
# --- URL MoMo sẽ chuyển hướng người dùng sau khi thanh toán xong ---
MOMO_REDIRECT_URL = f'{SERVER}' # Trang thông báo thành công

# --- Endpoint của MoMo (dùng môi trường test) ---
MOMO_ENDPOINT = 'https://test-payment.momo.vn/v2/gateway/api/create'

GOOGLE_API_KEY="AIzaSyDLm2z59TLtXOhuy8L6L2tN6uPXJHdhxhQ"

project_dir = os.path.dirname(__file__)
