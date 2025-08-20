# -*- coding: utf-8 -*-
# OFO/tests/test_historyOrder.py

import unittest
import hashlib
from datetime import datetime, timedelta
from __init__ import create_app, db
from models import User, Restaurant, Dish, Order, OrderDetail, UserRole, OrderState
from dao import get_orders_by_user_id

class HistoryOrderTestCase(unittest.TestCase):
    def setUp(self):
        """Thiết lập môi trường test với đầy đủ dữ liệu cần thiết."""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # --- Dựng "sân khấu" ---
        hashed_password = str(hashlib.md5('password'.encode('utf-8')).hexdigest())

        # 1. Tạo người dùng với đầy đủ thông tin
        user1 = User(name="user_with_history", email="user1@test.com", phone="0901000001", password=hashed_password, role=UserRole.USER)
        user2 = User(name="another_user", email="user2@test.com", phone="0901000002", password=hashed_password, role=UserRole.USER)
        user3_no_orders = User(name="user_no_history", email="user3@test.com", phone="0901000003", password=hashed_password, role=UserRole.USER)
        owner = User(name="owner", email="owner@test.com", phone="0901000004", password=hashed_password, role=UserRole.RESTAURANT)
        db.session.add_all([user1, user2, user3_no_orders, owner])
        db.session.commit()

        # 2. Tạo nhà hàng và món ăn
        restaurant = Restaurant(restaurant_name="Nhà hàng Lịch Sử", owner_user_id=owner.id)
        db.session.add(restaurant)
        db.session.commit()

        dish1 = Dish(name="Phở Đặc Biệt", price=50000.0, restaurant_id=restaurant.id)
        dish2 = Dish(name="Bún Chả Hà Nội", price=45000.0, restaurant_id=restaurant.id)
        db.session.add_all([dish1, dish2])
        db.session.commit()

        # --- 3. Tạo các đơn hàng (ĐÃ SỬA LẠI CHO ĐÚNG MODEL) ---
        shipping_fee = 15000.0

        # Đơn hàng MỚI NHẤT của user1 (đặt hôm nay)
        subtotal1 = dish1.price * 2
        order1_user1 = Order(
            user_id=user1.id, restaurant_id=restaurant.id, order_date=datetime.utcnow(),
            subtotal=subtotal1, shipping_fee=shipping_fee, total=subtotal1 + shipping_fee,
            delivery_address="123 Đường Mới, Q1", order_status=OrderState.COMPLETED
        )
        db.session.add(order1_user1)
        db.session.commit()
        detail1_order1 = OrderDetail(order_id=order1_user1.id, dish_id=dish1.id, quantity=2, price=dish1.price,
                                     dish_name=dish1.name, selected_options_luc_dat={})
        db.session.add(detail1_order1)

        # Đơn hàng CŨ HƠN của user1 (đặt hôm qua)
        subtotal2 = dish2.price * 1
        order2_user1 = Order(
            user_id=user1.id, restaurant_id=restaurant.id, order_date=datetime.utcnow() - timedelta(days=1),
            subtotal=subtotal2, shipping_fee=shipping_fee, total=subtotal2 + shipping_fee,
            delivery_address="456 Đường Cũ, Q2", order_status=OrderState.COMPLETED
        )
        db.session.add(order2_user1)
        db.session.commit()
        detail1_order2 = OrderDetail(order_id=order2_user1.id, dish_id=dish2.id, quantity=1, price=dish2.price,
                                     dish_name=dish2.name, selected_options_luc_dat={})
        db.session.add(detail1_order2)

        # Đơn hàng của user2 (để kiểm tra không bị lẫn)
        subtotal3 = dish1.price * 1
        order1_user2 = Order(
            user_id=user2.id, restaurant_id=restaurant.id, order_date=datetime.utcnow(),
            subtotal=subtotal3, shipping_fee=shipping_fee, total=subtotal3 + shipping_fee,
            delivery_address="789 Đường Khác, Q3", order_status=OrderState.PENDING
        )
        db.session.add(order1_user2)
        db.session.commit()
        detail1_order3 = OrderDetail(order_id=order1_user2.id, dish_id=dish1.id, quantity=1, price=dish1.price,
                                     dish_name=dish1.name, selected_options_luc_dat={})
        db.session.add(detail1_order3)

        db.session.commit()

        # Lưu lại các ID cần thiết
        self.user1_id = user1.id
        self.user3_id = user3_no_orders.id
        self.non_existent_user_id = 999

    def tearDown(self):
        """Dọn dẹp "sân khấu" sau mỗi lần test."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    # =================================================================
    # ===== CÁC BÀI TEST CHO CHỨC NĂNG LẤY LỊCH SỬ ĐƠN HÀNG =========
    # =================================================================

    def test_get_orders_for_user_with_history(self):
        """(LẤY) Kiểm tra lấy lịch sử đơn hàng cho người dùng có đơn hàng thành công."""
        print(f"\n--- Mục đích: {self.test_get_orders_for_user_with_history.__doc__} ---")

        orders = get_orders_by_user_id(self.user1_id)

        # 1. Kiểm tra số lượng đơn hàng trả về có đúng không (user1 có 2 đơn)
        self.assertIsNotNone(orders)
        self.assertEqual(len(orders), 2)

        # 2. Kiểm tra thứ tự sắp xếp (đơn mới nhất phải ở đầu danh sách)
        self.assertGreater(orders[0].order_date, orders[1].order_date)

        # 3. Kiểm tra dữ liệu đi kèm (eager loading) có hoạt động không
        first_order = orders[0]
        self.assertIsNotNone(first_order.restaurant)
        self.assertEqual(first_order.restaurant.restaurant_name, "Nhà hàng Lịch Sử")
        self.assertTrue(len(first_order.details) > 0)
        self.assertEqual(first_order.details[0].dish.name, "Phở Đặc Biệt")
        self.assertEqual(first_order.details[0].quantity, 2)

        print(">>> Kết quả: ĐÚNG - Lấy đúng 2 đơn hàng, sắp xếp chính xác và có đủ thông tin chi tiết.")

    def test_get_orders_for_user_with_no_history(self):
        """(LẤY) Kiểm tra lấy lịch sử cho người dùng chưa có đơn hàng nào."""
        print(f"\n--- Mục đích: {self.test_get_orders_for_user_with_no_history.__doc__} ---")

        orders = get_orders_by_user_id(self.user3_id)
        self.assertIsNotNone(orders)
        self.assertEqual(len(orders), 0)
        print(">>> Kết quả: ĐÚNG - Trả về danh sách rỗng.")

    def test_get_orders_for_nonexistent_user(self):
        """(LẤY) Kiểm tra lấy lịch sử cho một ID người dùng không tồn tại."""
        print(f"\n--- Mục đích: {self.test_get_orders_for_nonexistent_user.__doc__} ---")

        orders = get_orders_by_user_id(self.non_existent_user_id)
        self.assertIsNotNone(orders)
        self.assertEqual(len(orders), 0)
        print(">>> Kết quả: ĐÚNG - Trả về danh sách rỗng.")

if __name__ == '__main__':
    unittest.main()