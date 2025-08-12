# tests/test_notifications.py

import unittest
import json
import hashlib
from unittest.mock import patch
from __init__ import create_app, db
from models import User, UserRole, Restaurant, Category, Order, OrderState, Payment, PaymentStatus
from flask import url_for


class NotificationTestCase(unittest.TestCase):

    def setUp(self):
        """Hàm setUp chuẩn."""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        db.create_all()

        self.user = User(
            name='Khách Hàng Noti',
            email='customer_noti@test.com',
            phone='0123456789',
            password=str(hashlib.md5('password'.encode('utf-8')).hexdigest())
        )
        self.owner = User(
            name='Chủ Quán Noti',
            email='owner_noti@test.com',
            phone='0987654321',
            password=str(hashlib.md5('password_owner'.encode('utf-8')).hexdigest()),
            role=UserRole.RESTAURANT
        )
        db.session.add_all([self.user, self.owner])
        db.session.commit()

        self.restaurant = Restaurant(
            restaurant_name='Nhà hàng Noti',
            owner_user_id=self.owner.id,
            active=True
        )
        db.session.add(self.restaurant)
        db.session.commit()

        self.order = Order(
            user_id=self.user.id,
            restaurant_id=self.restaurant.id,
            subtotal=100000,
            total=100000,
            delivery_address='123 ABC',
            order_status=OrderState.UNPAID
        )
        db.session.add(self.order)
        db.session.commit()

        self.payment = Payment(
            order_id=self.order.id,
            amount=100000,
            payment_method='momo',
            payment_status=PaymentStatus.UNPAID
        )
        db.session.add(self.payment)
        db.session.commit()

    def tearDown(self):
        """Hàm tearDown chuẩn."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    @patch('dao.count_orders_for_restaurant_today')
    @patch('__init__.socketio.emit')  # Giả lập hàm emit của socketio
    def test_socketio_emits_on_successful_payment(self, mock_socketio_emit, mock_count_orders):
        """
        Kiểm thử: Socket.IO có gửi đi sự kiện 'new_order' khi MoMo IPN báo thành công.
        """
        # 1. Giả lập (mock) các hàm phụ thuộc
        mock_count_orders.return_value = 5  # Giả sử đây là đơn hàng thứ 5 trong ngày

        # 2. Tạo dữ liệu POST giả lập từ MoMo báo thanh toán thành công
        momo_success_payload = {
            'resultCode': 0,
            'message': 'Thành công.'
        }

        # 3. Gửi request đến IPN handler, mô phỏng việc MoMo gọi về
        self.client.post(url_for('main.momo_ipn_handler', payment_id=self.payment.id),
                         json=momo_success_payload)

        # 4. KIỂM TRA

        expected_data = {
            'order_id': self.order.id,
            'daily_order_number': 5,
            'total': '100,000đ',
            'customer_name': self.user.name
        }
        expected_room = f'restaurant_{self.restaurant.id}'

        # Kiểm tra xem hàm emit CÓ ĐƯỢC GỌI với đúng các tham số này hay không,
        mock_socketio_emit.assert_any_call('new_order', expected_data, room=expected_room)

        # Kiểm tra xem trạng thái đơn hàng trong CSDL đã được cập nhật đúng chưa
        updated_order = db.session.get(Order, self.order.id)
        self.assertEqual(updated_order.order_status, OrderState.PENDING)