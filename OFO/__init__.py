# __init__.py

from flask import Flask,session, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_admin import Admin
import cloudinary
import config
from flask_socketio import SocketIO,join_room
from sqlalchemy import event
from sqlalchemy.engine import Engine
import sqlite3
# Khởi tạo các extension "trống" (chưa gắn vào app nào)
db = SQLAlchemy()
login = LoginManager()
socketio = SocketIO()

#xử lý thông báo nhà hàng
@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")

@socketio.on('join_restaurant_room')
def handle_join_restaurant_room(data):
    restaurant_id = data.get('restaurant_id')
    if restaurant_id:
        room_name = f'restaurant_{restaurant_id}'
        join_room(room_name)
        print(f"SUCCESS: Client {request.sid} for Restaurant {restaurant_id} has joined room '{room_name}'")
    else:
        print(f"WARNING: Client {request.sid} did not provide a restaurant_id.")

# Định nghĩa user_loader MỘT LẦN ở đây. Flask-Login sẽ tự động sử dụng nó.
@login.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))


def create_app(config_name='development'):
    """Hàm khởi tạo ứng dụng Flask (Application Factory)."""
    app = Flask(__name__)

    # 1. Tải cấu hình từ file config.py
    app.config.from_object(config.config_by_name.get(config_name))

    # 2. Gắn các extension vào app vừa tạo
    db.init_app(app)
    login.init_app(app)
    socketio.init_app(app)
    # Cấu hình trang login cho Flask-Login, nó sẽ dùng blueprint 'main'
    login.login_view = 'main.login_view'

    # 3. Cấu hình Cloudinary
    cloudinary.config(
        cloud_name=app.config.get('CLOUDINARY_CLOUD_NAME'),
        api_key=app.config.get('CLOUDINARY_API_KEY'),
        api_secret=app.config.get('CLOUDINARY_API_SECRET')
    )

    # 4. Đăng ký trang Admin
    from admin import MyAdminIndexView, UserView, RestaurantPendingView
    from models import User,Restaurant
    admin_manager = Admin(app=app, name='Kymie Food', template_mode='bootstrap4', index_view=MyAdminIndexView())
    admin_manager.add_view(UserView(User, db.session, name='Người dùng'))
    admin_manager.add_view(RestaurantPendingView(Restaurant, db.session, name='Duyệt nhà hàng', endpoint='pending_restaurants'))

    # 5. Đăng ký các route thông thường qua Blueprint
    from index import main_bp  # Import Blueprint từ index.py
    app.register_blueprint(main_bp)

    return app
#bắt lỗi khóa ngoại
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()