# -*- coding: utf-8 -*-
# OFO/tests/test_momo.py

import unittest
import json
import hashlib
from unittest.mock import patch, MagicMock
from __init__ import create_app, db
from models import User, Restaurant, Dish, Order, Payment, OrderDetail, UserRole, OrderState, PaymentStatus

# Import các hàm cần test
from dao import create_order_from_cart, create_payment_record
from index import create_momo_payment_request

class MomoPaymentTestCase(unittest.TestCase):
    def setUp(self):
        """Thiết lập môi trường test."""
        self.app = create_app('testing')
        self.app.config.update({
            'MOMO_PARTNER_CODE': 'fake_partner_code',
            'MOMO_ACCESS_KEY': 'fake_access_key',
            'MOMO_SECRET_KEY': 'fake_secret_key',
            'MOMO_IPN_URL_BASE': 'https://example.com/ipn',
            'MOMO_REDIRECT_URL': 'https://example.com/redirect',
            'MOMO_ENDPOINT': 'https://test-payment.momo.vn/v2/gateway/api/create'
        })
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # --- Dựng "sân khấu" dữ liệu trong một giao dịch duy nhất ---
        hashed_password = str(hashlib.md5('password'.encode('utf-8')).hexdigest())

        user = User(name="momo_user", email="momo@test.com", phone="0902000001", password=hashed_password, role=UserRole.USER)
        owner = User(name="momo_owner", email="owner.momo@test.com", phone="0902000002", password=hashed_password, role=UserRole.RESTAURANT)
        db.session.add_all([user, owner])
        db.session.flush() # Lấy ID cho user và owner

        restaurant = Restaurant(restaurant_name="Quán MoMo", owner_user_id=owner.id, address="123 MoMo Street")
        db.session.add(restaurant)
        db.session.flush() # Lấy ID cho restaurant

        dish = Dish(name="Món ăn MoMo", price=100000.0, restaurant_id=restaurant.id)
        db.session.add(dish)

        # Commit tất cả mọi thứ một lần duy nhất
        db.session.commit()

        # Dữ liệu giỏ hàng giả
        self.cart_data = {
            'items': {
                'some_item_key': {
                    'dish_id': dish.id,
                    'name': dish.name,
                    'price': dish.price,
                    'quantity': 2,
                    'options': {},
                    'note': 'Ít cay'
                }
            }
        }
        self.user_id = user.id
        self.restaurant_id = restaurant.id

    def tearDown(self):
        """Dọn dẹp môi trường test."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    # =================================================================
    # ===== CÁC BÀI TEST CHO LUỒNG THANH TOÁN MOMO ===================
    # =================================================================

    def test_create_order_and_payment_record(self):
        """(MOMO-Setup) Kiểm tra tạo Order và Payment record thành công."""
        print(f"\n--- Mục đích: {self.test_create_order_and_payment_record.__doc__} ---")
        new_order = create_order_from_cart(
            user_id=self.user_id, restaurant_id=self.restaurant_id, cart_data=self.cart_data,
            delivery_address="123 Test Street", note="Giao nhanh", subtotal=200000,
            shipping_fee=15000, discount=0, delivery_time="30"
        )
        self.assertIsNotNone(new_order)
        self.assertEqual(db.session.query(Order).count(), 1)
        self.assertEqual(db.session.query(OrderDetail).count(), 1)
        self.assertEqual(new_order.total, 215000)

        payment = create_payment_record(new_order, 'momo')
        self.assertIsNotNone(payment)
        self.assertEqual(db.session.query(Payment).count(), 1)
        self.assertEqual(payment.order_id, new_order.id)
        self.assertEqual(payment.amount, 215000)
        self.assertEqual(payment.payment_status, PaymentStatus.UNPAID)
        print(">>> Kết quả: ĐÚNG - Tạo Order và Payment thành công.")

    # SỬA LỖI: Patch đúng vào 'dao.requests.post'
    @patch('dao.requests.post')
    def test_create_momo_request_success(self, mock_post):
        """(MOMO) Kiểm tra tạo yêu cầu thanh toán MoMo thành công."""
        print(f"\n--- Mục đích: {self.test_create_momo_request_success.__doc__} ---")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "resultCode": 0,
            "payUrl": "https://test-payment.momo.vn/v2/gateway/pay/12345"
        }
        mock_post.return_value = mock_response

        order = create_order_from_cart(
            user_id=self.user_id, restaurant_id=self.restaurant_id, cart_data=self.cart_data,
            delivery_address="123 Test Street", note="Giao nhanh", subtotal=200000,
            shipping_fee=15000, discount=0, delivery_time="30"
        )
        payment = create_payment_record(order, 'momo')

        pay_url = create_momo_payment_request(payment)

        self.assertEqual(pay_url, "https://test-payment.momo.vn/v2/gateway/pay/12345")
        updated_payment = db.session.get(Payment, payment.id)
        self.assertEqual(updated_payment.pay_url, "https://test-payment.momo.vn/v2/gateway/pay/12345")
        self.assertIsNotNone(updated_payment.momo_order_id)
        mock_post.assert_called_once()
        print(">>> Kết quả: ĐÚNG - Trả về payUrl và cập nhật DB thành công.")

    # SỬA LỖI: Patch đúng vào 'dao.requests.post'
    @patch('dao.requests.post')
    def test_create_momo_request_failure(self, mock_post):
        """(MOMO) Kiểm tra trường hợp MoMo API trả về lỗi."""
        print(f"\n--- Mục đích: {self.test_create_momo_request_failure.__doc__} ---")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "resultCode": 1001,
            "message": "Access denied"
        }
        mock_post.return_value = mock_response

        order = create_order_from_cart(
            user_id=self.user_id, restaurant_id=self.restaurant_id, cart_data=self.cart_data,
            delivery_address="123 Test Street", note="Giao nhanh", subtotal=200000,
            shipping_fee=15000, discount=0, delivery_time="30"
        )
        payment = create_payment_record(order, 'momo')

        pay_url = create_momo_payment_request(payment)

        self.assertIsNone(pay_url)
        print(">>> Kết quả: ĐÚNG - Trả về None khi MoMo báo lỗi.")

if __name__ == '__main__':
    unittest.main()