import unittest
from unittest.mock import patch, MagicMock
import hashlib
from __init__ import create_app, db
from models import User
from dao import auth_user


class TestAuthUser(unittest.TestCase):

    def setUp(self):
        """
        Thiết lập môi trường test trước mỗi hàm test.
        """
        # 1. Tạo ứng dụng với cấu hình 'testing'
        self.app = create_app('testing')

        # 2. Tạo một "application context" để có thể dùng `db` và `User.query`
        self.app_context = self.app.app_context()
        self.app_context.push()

        # 3. Tạo tất cả các bảng trong CSDL SQLite in-memory
        db.create_all()

        # 4. Tạo một người dùng mẫu để test
        self.test_phone = '0987654321'
        self.test_password_plain = 'matkhau123'

        # Băm mật khẩu giống hệt như trong hàm auth_user
        hashed_password = str(hashlib.md5(self.test_password_plain.encode('utf-8')).hexdigest())

        # Tạo và lưu người dùng vào CSDL test
        test_user = User(phone=self.test_phone, password=hashed_password, name='Test User', email='test@example.com')
        db.session.add(test_user)
        db.session.commit()

    def tearDown(self):
        """
        Dọn dẹp môi trường test sau mỗi hàm test.
        """
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_auth_user_success(self):
        """
        Trường hợp 1: Kiểm tra đăng nhập thành công với thông tin chính xác.
        """
        print("Running: test_auth_user_success")
        # Gọi hàm cần test với thông tin đúng
        user = auth_user(self.test_phone, self.test_password_plain)

        # Khẳng định (Assert) rằng người dùng được trả về không phải là None
        self.assertIsNotNone(user)
        # Khẳng định rằng đó đúng là người dùng chúng ta đã tạo
        self.assertEqual(user.phone, self.test_phone)
        self.assertEqual(user.name, 'Test User')

    def test_auth_user_wrong_password(self):
        """
        Trường hợp 2: Kiểm tra đăng nhập thất bại khi sai mật khẩu.
        """
        print("Running: test_auth_user_wrong_password")
        # Gọi hàm cần test với mật khẩu sai
        user = auth_user(self.test_phone, 'saimatkhau')

        # Khẳng định rằng kết quả trả về là None
        self.assertIsNone(user)

    def test_auth_user_nonexistent_phone(self):
        """
        Trường hợp 3: Kiểm tra đăng nhập thất bại khi số điện thoại không tồn tại.
        """
        print("Running: test_auth_user_nonexistent_phone")
        # Gọi hàm cần test với SĐT không có trong CSDL
        user = auth_user('0123456789', self.test_password_plain)

        # Khẳng định rằng kết quả trả về là None
        self.assertIsNone(user)

    def test_auth_user_with_whitespace_in_password(self):
        """
        Trường hợp 4: Kiểm tra hàm có xử lý khoảng trắng ở đầu/cuối mật khẩu.
        """
        print("Running: test_auth_user_with_whitespace_in_password")
        # Mật khẩu có khoảng trắng
        password_with_spaces = f"  {self.test_password_plain}  "

        # Gọi hàm, hàm này nên tự động `strip()` khoảng trắng
        user = auth_user(self.test_phone, password_with_spaces)

        # Khẳng định rằng đăng nhập vẫn thành công
        self.assertIsNotNone(user)
        self.assertEqual(user.phone, self.test_phone)

if __name__ == "__main__":
    unittest.main