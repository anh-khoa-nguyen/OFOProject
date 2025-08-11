import unittest
import hashlib
from __init__ import create_app, db
from models import User
from dao import auth_user

class AuthUserTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        self.test_phone = '0987654321'
        self.test_password_plain = 'matkhau123'
        hashed_password = str(hashlib.md5(self.test_password_plain.encode('utf-8')).hexdigest())
        test_user = User(phone=self.test_phone, password=hashed_password, name='Test User', email='test@example.com')
        db.session.add(test_user)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_auth_user_success(self):
        """Kiểm thử đăng nhập thành công."""
        user = auth_user(self.test_phone, self.test_password_plain)
        self.assertIsNotNone(user)
        self.assertEqual(user.phone, self.test_phone)

    def test_auth_user_wrong_password(self):
        """Kiểm thử đăng nhập thất bại khi sai mật khẩu."""
        user = auth_user(self.test_phone, 'saimatkhau')
        self.assertIsNone(user)

    def test_auth_user_nonexistent_phone(self):
        """Kiểm thử đăng nhập thất bại khi số điện thoại không tồn tại."""
        user = auth_user('0123456789', self.test_password_plain)
        self.assertIsNone(user)

    def test_auth_user_with_whitespace_in_password(self):
        """Kiểm thử hàm có xử lý khoảng trắng ở đầu/cuối mật khẩu."""
        password_with_spaces = f"  {self.test_password_plain}  "
        user = auth_user(self.test_phone, password_with_spaces)
        self.assertIsNotNone(user)

if __name__ == '__main__':
    unittest.main()