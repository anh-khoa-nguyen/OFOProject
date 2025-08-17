# OFO/tests/test_registration.py

import unittest
import hashlib
from __init__ import create_app, db
# Import đầy đủ các model cần thiết
from models import Category, User, Restaurant, UserRole
# Import các hàm DAO cần test
from dao import get_categories, register_restaurant_and_user


class RegistrationDaoTestCase(unittest.TestCase):
    def setUp(self):
        """Thiết lập môi trường test."""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # --- Dựng "sân khấu" ---
        # 1. Cần có sẵn một Category để dùng khi đăng ký nhà hàng
        category1 = Category(name="Đồ ăn nhanh")
        db.session.add(category1)

        # 2. Tạo sẵn một số User để kiểm tra các trường hợp trùng lặp
        existing_user_email = User(name="Test Email", email="existing@email.com", password="123")
        existing_user_phone = User(name="Test Phone", email="unique@email.com", password="123", phone="0123456789")
        db.session.add_all([existing_user_email, existing_user_phone])

        db.session.commit()

        # Lưu lại các ID và thông tin cần thiết
        self.category_id = category1.id
        self.existing_email = existing_user_email.email
        self.existing_phone = existing_user_phone.phone

    def tearDown(self):
        """Dọn dẹp sau mỗi test."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_get_categories_with_data(self):
        """(GET CATEGORY) Kiểm tra lấy danh sách category thành công khi có dữ liệu."""
        categories = get_categories()

        self.assertIsNotNone(categories)
        self.assertIsInstance(categories, list)
        # Chúng ta đã tạo 1 category trong setUp
        self.assertEqual(len(categories), 1)
        self.assertEqual(categories[0].name, "Đồ ăn nhanh")

    def test_get_categories_empty(self):
        """(GET CATEGORY) Kiểm tra lấy danh sách category khi không có dữ liệu."""
        # Xóa hết category đã tạo trong setUp để giả lập DB rỗng
        Category.query.delete()
        db.session.commit()

        categories = get_categories()

        self.assertIsNotNone(categories)
        self.assertIsInstance(categories, list)
        self.assertEqual(len(categories), 0)


    def test_register_success(self):
        """(REGISTER) Kiểm tra đăng ký nhà hàng và người dùng mới thành công."""
        is_success, result_obj = register_restaurant_and_user(
            username="Chủ Quán Mới",
            email="new.owner@email.com",
            password="new_password",
            phone="0987654321",
            res_name="Quán Ăn Ngon",
            address="123 Đường ABC",
            description="Món ăn đa dạng",
            open_time="08:00",
            close_time="22:00",
            category_id=self.category_id
        )

        # 1. Kiểm tra kết quả trả về
        self.assertTrue(is_success)
        self.assertIsInstance(result_obj, User)

        # 2. Kiểm tra dữ liệu đã thực sự được tạo trong DB chưa
        new_user = User.query.filter_by(email="new.owner@email.com").first()
        new_restaurant = Restaurant.query.filter_by(restaurant_name="Quán Ăn Ngon").first()

        self.assertIsNotNone(new_user)
        self.assertIsNotNone(new_restaurant)

        # 3. Kiểm tra User được tạo có đúng vai trò và mật khẩu đã mã hóa không
        self.assertEqual(new_user.role, UserRole.RESTAURANT)
        self.assertEqual(new_user.password, hashlib.md5("new_password".encode('utf-8')).hexdigest())

        # 4. Kiểm tra Restaurant có được liên kết đúng với User không
        self.assertEqual(new_restaurant.owner_user_id, new_user.id)

    def test_register_fails_with_duplicate_email(self):
        """(REGISTER) Kiểm tra đăng ký thất bại do email đã tồn tại."""
        user_count_before = User.query.count()

        is_success, message = register_restaurant_and_user(
            username="Người Dùng Thừa",
            email=self.existing_email,  # Dùng email đã tồn tại
            password="123",
            phone="0111222333",
            res_name="Quán Trùng Lặp",
            address="456 XYZ",
            description="",
            open_time="09:00",
            close_time="21:00",
            category_id=self.category_id
        )

        user_count_after = User.query.count()

        self.assertFalse(is_success)
        self.assertEqual(message, 'Email này đã được sử dụng cho một tài khoản khác.')
        # Đảm bảo không có user mới nào được tạo ra
        self.assertEqual(user_count_before, user_count_after)

    def test_register_fails_with_duplicate_phone(self):
        """(REGISTER) Kiểm tra đăng ký thất bại do số điện thoại đã tồn tại."""
        user_count_before = User.query.count()

        is_success, message = register_restaurant_and_user(
            username="Người Dùng Thừa 2",
            email="another.unique@email.com",
            password="123",
            phone=self.existing_phone,  # Dùng SĐT đã tồn tại
            res_name="Quán Trùng Lặp 2",
            address="789 LMN",
            description="",
            open_time="10:00",
            close_time="20:00",
            category_id=self.category_id
        )

        user_count_after = User.query.count()

        self.assertFalse(is_success)
        self.assertEqual(message, 'Số điện thoại này đã được đăng ký.')
        # Đảm bảo không có user mới nào được tạo ra
        self.assertEqual(user_count_before, user_count_after)


if __name__ == '__main__':
    unittest.main()