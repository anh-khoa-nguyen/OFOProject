import os
from urllib.parse import quote

# SERVER = 'https://workable-primarily-ferret.ngrok-free.app'
#
# MOMO_PARTNER_CODE = 'MOMO'
# MOMO_ACCESS_KEY = 'F8BBA842ECF85'
# MOMO_SECRET_KEY = 'K951B6PE1waDMi640xX08PD3vg6EkVlz'
#
# # --- URL MoMo sẽ gọi về server của bạn ---
# # Thay 'https://yourdomain.com' bằng tên miền thực tế của bạn khi triển khai
# # IPN_URL_BASE = 'https://yourdomain.com/momo/ipn-handler'
# MOMO_IPN_URL_BASE = f'{SERVER}/momo/confirm-payment'
# MOMO_REDIRECT_URL = f'{SERVER}'  # Trang thông báo thành công
#
# # --- Endpoint của MoMo (dùng môi trường test) ---
# MOMO_ENDPOINT = 'https://test-payment.momo.vn/v2/gateway/api/create'
#
# GOOGLE_API_KEY = "AIzaSyDLm2z59TLtXOhuy8L6L2tN6uPXJHdhxhQ"


class Config:
    """Cấu hình cơ bản"""
    SECRET_KEY = 'SDASDEW!21321321s2'
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SO_PHAN_TU = 10
    CLOUDINARY_CLOUD_NAME = "dq2jtbrda"
    CLOUDINARY_API_KEY = "341769211452564"
    CLOUDINARY_API_SECRET = "_5G4itRP_2YE52K8srR6cJO5Las"

class DevelopmentConfig(Config):
    """Cấu hình cho môi trường phát triển"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:%s@localhost/ofodb?charset=utf8mb4" % quote('Abc@123')
    SERVER = 'https://workable-primarily-ferret.ngrok-free.app'

    MOMO_PARTNER_CODE = 'MOMO'
    MOMO_ACCESS_KEY = 'F8BBA842ECF85'
    MOMO_SECRET_KEY = 'K951B6PE1waDMi640xX08PD3vg6EkVlz'
    MOMO_IPN_URL_BASE = f'{SERVER}/momo/confirm-payment'
    MOMO_REDIRECT_URL = f'{SERVER}'  # Trang thông báo thành công
    MOMO_ENDPOINT = 'https://test-payment.momo.vn/v2/gateway/api/create'
    GOOGLE_API_KEY = "AIzaSyDLm2z59TLtXOhuy8L6L2tN6uPXJHdhxhQ"

class TestingConfig(Config):
    """Cấu hình cho môi trường test"""
    TESTING = True
    # Sử dụng SQLite in-memory cho test
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    # Tắt CSRF trong form khi test (nếu bạn dùng Flask-WTF)
    WTF_CSRF_ENABLED = False
    SERVER_NAME = 'localhost.test'
    MOMO_PARTNER_CODE = "DUMMY_CODE"
    MOMO_ACCESS_KEY = "DUMMY_KEY"
    MOMO_SECRET_KEY = "DUMMY_SECRET"
    MOMO_ENDPOINT = "https://test-payment.momo.vn/v2/gateway/api/create"
    MOMO_IPN_URL_BASE = "http://localhost.test/momo"
    MOMO_REDIRECT_URL = "http://localhost.test"

# Dictionary để dễ dàng truy cập các lớp config
config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig
}

project_dir = os.path.dirname(__file__)
