from flask_admin import Admin,AdminIndexView,expose
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user, logout_user
from wtforms.fields import SelectField
from __init__ import db
from models import User, UserRole, Restaurant
from wtforms import FileField
import cloudinary.uploader
from flask import redirect,url_for,request,flash
from flask_admin.actions import action

class AdminAccess:
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == UserRole.ADMIN

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('main.login_view', next=request.url))

class MyAdminIndexView(AdminAccess,AdminIndexView):
    @expose('/')
    def index(self):
        return self.render('admin/index.html')
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == UserRole.ADMIN

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('main.login_view', next=request.url))


# admin = Admin(app=app, name='Kymie Food', template_mode='bootstrap4',index_view=MyAdminIndexView())

from flask_admin.contrib.sqla import ModelView
from wtforms import PasswordField
from werkzeug.security import generate_password_hash

import hashlib

def hash_password_md5(password: str) -> str:
    return hashlib.md5(password.strip().encode('utf-8')).hexdigest()


class AdminSecureView(AdminAccess, ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == UserRole.ADMIN

    def inaccessible_callback(self, name, **kwargs):
        flash("Bạn không có quyền truy cập trang quản trị!", "danger")
        return redirect(url_for('main.login_view', next=request.url))

class UserView(AdminSecureView):
    column_labels = {
        'name': 'Họ tên',
        'email': 'Email',
        'phone': 'Số điện thoại',
        'role': 'Vai trò',
        'avatar': 'Ảnh đại diện',
        'active': 'Trạng thái',
    }
    column_filters = ['role']

    form_overrides = {
        'role': SelectField
    }

    form_args = {
        'role': {
            'label': 'Vai trò',
            'choices': [
                (UserRole.USER.value, 'Người dùng'),
                (UserRole.RESTAURANT.value, 'Nhà hàng'),
                (UserRole.ADMIN.value, 'Quản trị viên')
            ],
            'coerce': lambda x: UserRole(x)
        }
    }
    form_extra_fields = {
        'avatar_file': FileField('Tải ảnh đại diện')
    }



    def on_model_change(self, form, model, is_created):
        avatar_file = form.avatar_file.data
        if avatar_file:
            upload_result = cloudinary.uploader.upload(avatar_file)
            model.avatar = upload_result.get('secure_url')
        if is_created:
            if form.password.data:
                model.password = hash_password_md5(form.password.data.strip())

        if isinstance(form.role.data, str):
            model.role = UserRole(form.role.data)

    form_excluded_columns = ['password']
    column_exclude_list = ['password','avatar']


# admin.py

# ... (các import và các class View khác của bạn) ...
from models import Restaurant, User, UserRole
from sqlalchemy import inspect as sa_inspect  # Import inspect để lấy tên cột


class RestaurantPendingView(AdminSecureView):
    can_create = False
    can_edit = True
    can_delete = True

    # 1. HIỂN THỊ CỘT 'user' (Tên của relationship trong model Restaurant)
    column_list = ['restaurant_name', 'user', 'address', 'active']
    column_labels = {
        'restaurant_name': 'Tên nhà hàng',
        'user': 'Chủ sở hữu',
        'address': 'Địa chỉ',
        'active': 'Trạng thái'
    }

    # 2. BỔ SUNG TÌM KIẾM THEO TÊN VÀ SĐT CỦA CHỦ SỞ HỮU
    # Cú pháp 'user.name' và 'user.phone' ở đây là hoàn toàn hợp lệ
    # Flask-Admin sẽ tự động tạo câu lệnh JOIN
    column_searchable_list = ['restaurant_name', 'user.name', 'user.phone']

    # Bổ sung bộ lọc theo tên và SĐT của chủ sở hữu
    column_filters = ['active', 'user.name', 'user.phone']
    def search_placeholder(self):
        return 'Tìm theo tên nhà hàng, tên hoặc SĐT chủ sở hữu'

    # --- CÁC THUỘC TÍNH KHÁC GIỮ NGUYÊN ---
    form_columns = ['active']
    form_edit_rules = ('active',)

    def get_query(self):
        return super().get_query().filter(Restaurant.active == False)

    def get_count_query(self):
        return super().get_count_query().filter(Restaurant.active == False)

    @action('approve', 'Duyệt nhà hàng', 'Bạn có chắc muốn duyệt các nhà hàng đã chọn?')
    def action_approve(self, ids):
        try:
            query = Restaurant.query.filter(Restaurant.id.in_(ids))
            count = 0
            for restaurant in query.all():
                if not restaurant.active:
                    restaurant.active = True
                    if restaurant.user and not restaurant.user.active:
                        restaurant.user.active = True
                    count += 1
            db.session.commit()
            flash(f'Đã duyệt thành công {count} nhà hàng.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Có lỗi xảy ra khi duyệt nhà hàng: {str(e)}', 'error')
# admin.add_view(RestaurantPendingView(User, db.session, name='Duyệt nhà hàng', endpoint='pending_users'))


