# -*- coding: utf-8 -*-
# OFO/tests/test_restaurant_dao.py

import unittest
import hashlib
from __init__ import create_app, db
from models import Restaurant, User, UserRole
from dao import load_random_restaurants
from sqlalchemy import func


class RestaurantDaoTestCase(unittest.TestCase):
    def setUp(self):
        """Thiết lập môi trường test với đầy đủ dữ liệu cần thiết."""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # --- Dựng "sân khấu" (ĐÃ SỬA LẠI CHO ĐÚNG MODEL) ---
        # 1. Tạo người dùng chủ nhà hàng với đầy đủ thông tin
        hashed_password = str(hashlib.md5('password'.encode('utf-8')).hexdigest())
        test_user = User(name="testowner", email="owner@test.com", phone="0909090909",
                         password=hashed_password, role=UserRole.RESTAURANT)
        db.session.add(test_user)
        db.session.commit()

        # 2. Tạo một loạt nhà hàng để test
        restaurant1 = Restaurant(restaurant_name="Nhà hàng A", owner_user_id=test_user.id, address="123 A Street",
                                 lat=10.776529, lng=106.700988)  # Gần trung tâm TPHCM
        restaurant2 = Restaurant(restaurant_name="Nhà hàng B", owner_user_id=test_user.id, address="456 B Street",
                                 lat=10.823099, lng=106.629670)  # Gần sân bay
        restaurant3 = Restaurant(restaurant_name="Nhà hàng C", owner_user_id=test_user.id, address="789 C Street",
                                 lat=21.027764, lng=105.834160)  # Hà Nội
        restaurant4 = Restaurant(restaurant_name="Nhà hàng D không tọa độ", owner_user_id=test_user.id,
                                 address="101 D Street")  # Nhà hàng không có lat, lng
        restaurant5 = Restaurant(restaurant_name="Nhà hàng E", owner_user_id=test_user.id, address="123 A Street",
                                 lat=10.776529, lng=106.700988)  # Trùng tọa độ với A

        db.session.add_all([restaurant1, restaurant2, restaurant3, restaurant4, restaurant5])
        db.session.commit()

    def tearDown(self):
        """Dọn dẹp "sân khấu" sau mỗi lần test."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    # =================================================================
    # ===== CÁC BÀI TEST CHO CHỨC NĂNG LOAD NHÀ HÀNG NGẪU NHIÊN =======
    # =================================================================

    def test_load_random_restaurants_no_location(self):
        """(LẤY) Kiểm tra lấy danh sách nhà hàng ngẫu nhiên thành công mà không có tọa độ người dùng."""
        print(f"\n--- Mục đích: {self.test_load_random_restaurants_no_location.__doc__} ---")

        restaurants = load_random_restaurants(limit=3)

        self.assertIsNotNone(restaurants)
        self.assertEqual(len(restaurants), 3)
        # Kiểm tra xem các thuộc tính khoảng cách và thời gian giao hàng có tồn tại không
        for r in restaurants:
            self.assertFalse(hasattr(r, 'distance_km'))
            self.assertFalse(hasattr(r, 'delivery_time'))

        print(">>> Kết quả: ĐÚNG - Lấy 3 nhà hàng ngẫu nhiên thành công, không có thông tin khoảng cách.")

    def test_load_random_restaurants_with_location(self):
        """(LẤY) Kiểm tra lấy nhà hàng và tính toán khoảng cách, thời gian giao hàng thành công."""
        print(f"\n--- Mục đích: {self.test_load_random_restaurants_with_location.__doc__} ---")

        user_lat = 10.775834
        user_lng = 106.701855

        restaurants = load_random_restaurants(limit=5, user_lat=user_lat, user_lng=user_lng)

        self.assertIsNotNone(restaurants)
        self.assertEqual(len(restaurants), 5)

        found_restaurant_a = False
        for r in restaurants:
            self.assertTrue(hasattr(r, 'distance_km'))
            self.assertTrue(hasattr(r, 'delivery_time'))

            if r.restaurant_name == "Nhà hàng A":
                found_restaurant_a = True
                self.assertIsNotNone(r.distance_km)
                self.assertIsNotNone(r.delivery_time)
                self.assertGreater(r.distance_km, 0)
                expected_time = round(10 + (r.distance_km * 5))
                self.assertEqual(r.delivery_time, expected_time)
                print(f"    - Nhà hàng A: Khoảng cách={r.distance_km}km, Thời gian giao hàng={r.delivery_time} phút")

            if r.restaurant_name == "Nhà hàng D không tọa độ":
                self.assertIsNone(r.distance_km)
                self.assertIsNone(r.delivery_time)
                print(f"    - Nhà hàng D: Khoảng cách và thời gian là None (đúng như mong đợi)")

        # Đảm bảo rằng nhà hàng A (có tọa độ) luôn nằm trong kết quả để có thể kiểm tra
        if not found_restaurant_a:
            # Nếu trong 5 nhà hàng ngẫu nhiên không có nhà hàng A, ta tìm nó một cách tường minh để test
            res_a = db.session.get(Restaurant, 1)  # Giả định ID là 1
            load_random_restaurants(limit=1, user_lat=user_lat, user_lng=user_lng)  # Gọi hàm để tính toán cho nó
            self.assertIsNotNone(res_a.distance_km)

        print(">>> Kết quả: ĐÚNG - Tính toán khoảng cách và thời gian giao hàng chính xác.")

    def test_load_restaurants_limit_parameter(self):
        """(LẤY) Kiểm tra tham số `limit` hoạt động chính xác."""
        print(f"\n--- Mục đích: {self.test_load_restaurants_limit_parameter.__doc__} ---")

        restaurants_limit_2 = load_random_restaurants(limit=2)
        self.assertEqual(len(restaurants_limit_2), 2)

        restaurants_limit_5 = load_random_restaurants(limit=5)
        self.assertEqual(len(restaurants_limit_5), 5)

        # Kiểm tra trường hợp limit lớn hơn số lượng nhà hàng có trong DB (ĐÃ SỬA LẠI CÚ PHÁP)
        restaurants_limit_100 = load_random_restaurants(limit=100)
        total_restaurants = db.session.query(Restaurant).count()
        self.assertEqual(len(restaurants_limit_100), total_restaurants)
        print(f">>> Kết quả: ĐÚNG - Tham số limit hoạt động chính xác (yêu cầu 2, 5, và >{total_restaurants}).")


if __name__ == '__main__':
    unittest.main()