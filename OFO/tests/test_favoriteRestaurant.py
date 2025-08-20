# -*- coding: utf-8 -*-
# OFO/tests/test_favoriteRestaurant.py

import unittest
import hashlib
from __init__ import create_app, db
from models import User, Restaurant, UserRole
from dao import toggle_favorite, is_favorite

class FavoriteRestaurantTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

        self.customer_password_plain = 'password123'
        hashed_password = str(hashlib.md5(self.customer_password_plain.encode('utf-8')).hexdigest())

        user_customer = User(name="Khach Hang Test", email="customer.fav@test.com", phone="0912345678",
                             password=hashed_password, role=UserRole.USER)
        user_owner = User(name="Chu Quan Test", email="owner.fav@test.com", phone="0987654321",
                          password=hashed_password, role=UserRole.RESTAURANT)
        db.session.add_all([user_customer, user_owner])
        db.session.commit()

        restaurant_a = Restaurant(restaurant_name="Nhà hàng Yêu Thích A", owner_user_id=user_owner.id)
        restaurant_b = Restaurant(restaurant_name="Nhà hàng Khác B", owner_user_id=user_owner.id)
        db.session.add_all([restaurant_a, restaurant_b])
        db.session.commit()

        user_customer.favorite_restaurants.append(restaurant_a)
        db.session.commit()

        self.customer_id = user_customer.id
        self.customer_phone = user_customer.phone
        self.restaurant_a_id = restaurant_a.id
        self.restaurant_b_id = restaurant_b.id

    def tearDown(self):
        """Dọn dẹp "sân khấu" sau mỗi lần test."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_is_favorite_returns_true_for_favorited(self):
        """(KIỂM TRA) is_favorite trả về True khi nhà hàng đã được yêu thích."""
        print(f"\n--- Mục đích: {self.test_is_favorite_returns_true_for_favorited.__doc__} ---")
        self.assertTrue(is_favorite(self.customer_id, self.restaurant_a_id))
        print(">>> Kết quả: ĐÚNG")

    def test_is_favorite_returns_false_for_not_favorited(self):
        """(KIỂM TRA) is_favorite trả về False khi nhà hàng chưa được yêu thích."""
        print(f"\n--- Mục đích: {self.test_is_favorite_returns_false_for_not_favorited.__doc__} ---")
        self.assertFalse(is_favorite(self.customer_id, self.restaurant_b_id))
        print(">>> Kết quả: ĐÚNG")

    def test_toggle_favorite_adds_new_favorite(self):
        """(TOGGLE) Kiểm tra thêm một nhà hàng mới vào danh sách yêu thích."""
        print(f"\n--- Mục đích: {self.test_toggle_favorite_adds_new_favorite.__doc__} ---")
        self.assertFalse(is_favorite(self.customer_id, self.restaurant_b_id))
        result = toggle_favorite(self.customer_id, self.restaurant_b_id)
        self.assertEqual(result, 'added')
        self.assertTrue(is_favorite(self.customer_id, self.restaurant_b_id))
        print(">>> Kết quả: ĐÚNG - Đã thêm thành công.")

    def test_toggle_favorite_removes_existing_favorite(self):
        """(TOGGLE) Kiểm tra xóa một nhà hàng đã có khỏi danh sách yêu thích."""
        print(f"\n--- Mục đích: {self.test_toggle_favorite_removes_existing_favorite.__doc__} ---")
        self.assertTrue(is_favorite(self.customer_id, self.restaurant_a_id))
        result = toggle_favorite(self.customer_id, self.restaurant_a_id)
        self.assertEqual(result, 'removed')
        self.assertFalse(is_favorite(self.customer_id, self.restaurant_a_id))
        print(">>> Kết quả: ĐÚNG - Đã xóa thành công.")

    def test_toggle_favorite_with_invalid_ids_raises_error(self):
        """(TOGGLE) Kiểm tra hàm báo lỗi khi ID không hợp lệ."""
        print(f"\n--- Mục đích: {self.test_toggle_favorite_with_invalid_ids_raises_error.__doc__} ---")
        with self.assertRaises(ValueError):
            toggle_favorite(999, self.restaurant_a_id)
        with self.assertRaises(ValueError):
            toggle_favorite(self.customer_id, 999)
        print(">>> Kết quả: ĐÚNG - Đã ném ra ValueError như mong đợi.")

    # =================================================================
    # ===== CÁC BÀI TEST CHO ROUTE /my-favorites (CẦN TEST CLIENT) ===
    # =================================================================

    def test_favorite_page_redirects_if_not_logged_in(self):
        """(ROUTE) Trang /my-favorites chuyển hướng đến trang đăng nhập nếu chưa đăng nhập."""
        print(f"\n--- Mục đích: {self.test_favorite_page_redirects_if_not_logged_in.__doc__} ---")
        response = self.client.get('/my-favorites')
        self.assertEqual(response.status_code, 302)
        print(">>> Kết quả: ĐÚNG - Chuyển hướng thành công.")

    def test_favorite_page_shows_correct_restaurants(self):
        """(ROUTE) Trang /my-favorites hiển thị đúng danh sách nhà hàng yêu thích khi đã đăng nhập."""
        print(f"\n--- Mục đích: {self.test_favorite_page_shows_correct_restaurants.__doc__} ---")

        with self.client:
            login_response = self.client.post('/login', data=dict(
                phone=self.customer_phone,
                password=self.customer_password_plain
            ), follow_redirects=True)
            self.assertEqual(login_response.status_code, 200)

            response = self.client.get('/my-favorites')
            self.assertEqual(response.status_code, 200)

            # Kiểm tra nội dung trang có đúng không (đã sửa)
            self.assertIn('Nhà hàng Yêu Thích A'.encode('utf-8'), response.data)
            self.assertNotIn('Nhà hàng Khác B'.encode('utf-8'), response.data)

            print(">>> Kết quả: ĐÚNG - Hiển thị đúng nhà hàng đã yêu thích.")

if __name__ == '__main__':
    unittest.main()