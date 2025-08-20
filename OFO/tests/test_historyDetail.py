# -*- coding: utf-8 -*-
# OFO/tests/test_historyDetail.py

import unittest
import hashlib
from datetime import datetime
from __init__ import create_app, db
from models import User, Restaurant, Dish, Order, OrderDetail, UserRole, OrderState
from dao import get_order_details_by_id


class HistoryDetailTestCase(unittest.TestCase):
    def setUp(self):
        """Thiết lập môi trường test với đầy đủ dữ liệu cần thiết."""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # --- Dựng "sân khấu" ---
        hashed_password = str(hashlib.md5('password'.encode('utf-8')).hexdigest())

        # 1. Tạo người dùng (khách hàng và chủ quán) với đầy đủ thông tin
        user_customer = User(name="customer_detail_test", email="customer@test.com", phone="0900000001",
                             password=hashed_password, role=UserRole.USER)
        user_owner = User(name="owner_detail_test", email="owner@test.com", phone="0900000002",
                          password=hashed_password, role=UserRole.RESTAURANT)
        db.session.add_all([user_customer, user_owner])
        db.session.commit()

        # 2. Tạo nhà hàng và món ăn
        restaurant = Restaurant(restaurant_name="Nhà hàng Chi Tiết", owner_user_id=user_owner.id)
        db.session.add(restaurant)
        db.session.commit()

        dish1 = Dish(name="Cơm Tấm Sườn Bì Chả", price=55000.0, restaurant_id=restaurant.id)
        dish2 = Dish(name="Trà Đá", price=5000.0, restaurant_id=restaurant.id)
        db.session.add_all([dish1, dish2])
        db.session.commit()

        # 3. Tạo một đơn hàng hoàn chỉnh để test (ĐÃ SỬA LẠI CHO ĐÚNG MODEL)
        order_subtotal = (dish1.price * 2) + dish2.price  # (55000 * 2) + 5000 = 115000
        shipping_fee = 15000.0
        order_total = order_subtotal + shipping_fee

        test_order = Order(
            user_id=user_customer.id,
            restaurant_id=restaurant.id,
            order_date=datetime.utcnow(),
            subtotal=order_subtotal,
            shipping_fee=shipping_fee,
            total=order_total,
            delivery_address="123 Đường Test, Phường Test, Quận Test, TP.HCM",
            order_status=OrderState.PENDING
        )
        db.session.add(test_order)
        db.session.commit()  # Commit để lấy được order.id

        detail1 = OrderDetail(order_id=test_order.id, dish_id=dish1.id, quantity=2, price=dish1.price,
                              dish_name=dish1.name, selected_options_luc_dat={})
        detail2 = OrderDetail(order_id=test_order.id, dish_id=dish2.id, quantity=1, price=dish2.price,
                              dish_name=dish2.name, selected_options_luc_dat={})
        db.session.add_all([detail1, detail2])
        db.session.commit()

        self.valid_order_id = test_order.id
        self.non_existent_order_id = 999

    def tearDown(self):
        """Dọn dẹp "sân khấu" sau mỗi lần test."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    # =================================================================
    # ===== CÁC BÀI TEST CHO CHỨC NĂNG LẤY CHI TIẾT ĐƠN HÀNG =========
    # =================================================================

    def test_get_details_for_existing_order(self):
        """(LẤY) Kiểm tra lấy chi tiết một đơn hàng tồn tại thành công."""
        print(f"\n--- Mục đích: {self.test_get_details_for_existing_order.__doc__} ---")

        order = get_order_details_by_id(self.valid_order_id)

        # 1. Kiểm tra có tìm thấy đơn hàng không
        self.assertIsNotNone(order)
        self.assertIsInstance(order, Order)
        self.assertEqual(order.id, self.valid_order_id)
        self.assertEqual(order.total, 130000.0)  # (115000 + 15000)

        # 2. Kiểm tra dữ liệu nhà hàng (joinedload) có được tải không
        self.assertIsNotNone(order.restaurant)
        self.assertEqual(order.restaurant.restaurant_name, "Nhà hàng Chi Tiết")

        # 3. Kiểm tra dữ liệu người dùng (joinedload) có được tải không
        self.assertIsNotNone(order.user)
        self.assertEqual(order.user.name, "customer_detail_test")

        # 4. Kiểm tra chi tiết đơn hàng (joinedload lồng) có được tải không
        self.assertIsNotNone(order.details)
        self.assertEqual(len(order.details), 2)

        # 5. Kiểm tra TẤT CẢ các món trong chi tiết một cách chính xác
        expected_items = {
            "Cơm Tấm Sườn Bì Chả": {"quantity": 2, "price": 55000.0},
            "Trà Đá": {"quantity": 1, "price": 5000.0}
        }

        actual_items = {detail.dish.name: {"quantity": detail.quantity, "price": detail.price} for detail in
                        order.details}

        self.assertDictEqual(actual_items, expected_items, "Chi tiết các món ăn trong đơn hàng không khớp.")

        print(">>> Kết quả: ĐÚNG - Lấy chi tiết đơn hàng thành công với đầy đủ thông tin liên quan.")

    def test_get_details_for_nonexistent_order(self):
        """(LẤY) Kiểm tra lấy chi tiết cho một ID đơn hàng không tồn tại."""
        print(f"\n--- Mục đích: {self.test_get_details_for_nonexistent_order.__doc__} ---")

        order = get_order_details_by_id(self.non_existent_order_id)

        # Phải trả về None vì không tìm thấy
        self.assertIsNone(order)

        print(">>> Kết quả: ĐÚNG - Trả về None khi không tìm thấy đơn hàng.")


if __name__ == '__main__':
    unittest.main()