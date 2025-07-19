# from flask_admin import Admin, BaseView
# from models import *
# from flask_admin.contrib.sqla import ModelView
# from flask_login import current_user,logout_user
#
# admin = Admin(app=app, name='Kymie Food', template_mode='bootstrap4')
#
#
# class AdminView(ModelView):
#     page_size = 10
#
#     def is_accessible(self):  # Được phép truy cập nếu như, còn không thì ẩn
#         return current_user.is_authenticated and current_user.vaitro == UserRole.ADMIN
#
# admin.add_view(AdminView(User, db.session, name='Người dùng'))

