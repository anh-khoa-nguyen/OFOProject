from flask_admin import Admin,AdminIndexView,expose
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user, logout_user
from wtforms.fields import SelectField
from __init__ import app, db
from models import User, UserRole
from wtforms import FileField
import cloudinary.uploader
from flask import redirect,url_for,request,flash
from flask_admin.actions import action

class AdminAccess:
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == UserRole.ADMIN

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login', next=request.url))

class MyAdminIndexView(AdminAccess,AdminIndexView):
    @expose('/')
    def index(self):
        return self.render('admin/index.html')
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == UserRole.ADMIN

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login_view', next=request.url))


admin = Admin(app=app, name='Kymie Food', template_mode='bootstrap4',index_view=MyAdminIndexView())

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
        return redirect(url_for('login', next=request.url))

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

class RestaurantPendingView(AdminSecureView):
    can_create = False
    can_edit = True
    can_delete = False

    column_labels = {
        'name': 'Tên nhà hàng',
        'email': 'Email',
        'phone': 'Số điện thoại',
        'active': 'Trạng thái',
    }

    column_list = ['name', 'email', 'phone', 'active']
    form_excluded_columns = ['avatar']
    form_columns = ['active']

    def get_query(self):
        return super().get_query().filter(User.role == UserRole.RESTAURANT, User.active == False)

    def get_count_query(self):
        return super().get_count_query().filter(User.role == UserRole.RESTAURANT, User.active == False)

    def on_model_change(self, form, model, is_created):
        if isinstance(form.role.data, str):
            model.role = UserRole(form.role.data)

    @action('approve', 'Duyệt', 'Bạn có chắc muốn duyệt các nhà hàng đã chọn không?')
    def action_approve(self, ids):
        try:
            query = User.query.filter(User.id.in_(ids))
            count = 0
            for user in query.all():
                if user.role == UserRole.RESTAURANT and not user.active:
                    user.active = True
                    count += 1
            db.session.commit()
            flash(f'Đã duyệt {count} nhà hàng.', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Có lỗi xảy ra khi duyệt nhà hàng.', 'error')


admin.add_view(UserView(User, db.session, name='Người dùng'))
admin.add_view(RestaurantPendingView(User, db.session, name='Duyệt nhà hàng', endpoint='pending_users'))


