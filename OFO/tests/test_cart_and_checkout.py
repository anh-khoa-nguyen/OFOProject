# tests/test_cart_and_checkout.py

import unittest
import json
import hashlib
from __init__ import create_app, db
from models import User, UserRole, Restaurant, Category, Dish, Order, OrderDetail
from flask import session, url_for
from unittest.mock import patch


class CartAndCheckoutTestCase(unittest.TestCase):

    def setUp(self):
        """Hàm setUp chuẩn cho tất cả các test."""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        db.create_all()

        self.user1_pass = 'user123'
        self.user1 = User(name='Khách Hàng Test', email='customer@test.com', phone='0909090909',
                          password=str(hashlib.md5(self.user1_pass.encode('utf-8')).hexdigest()))
        self.owner = User(name='Chủ Quán Test', email='owner@test.com', phone='0808080808', password='pass',
                          role=UserRole.RESTAURANT)
        self.owner2 = User(name='Chủ Quán Test2', email='owne2r@test.com', phone='0808080807', password='pass',
                          role=UserRole.RESTAURANT)
        db.session.add_all([self.user1, self.owner,self.owner2])
        db.session.commit()

        self.category = Category(name='Đồ ăn test')
        db.session.add(self.category)
        db.session.commit()

        self.restaurant1 = Restaurant(restaurant_name='Nhà hàng A', owner_user_id=self.owner.id,
                                      category_id=self.category.id, active=True, lat=10.0, lng=106.0)
        self.restaurant2 = Restaurant(restaurant_name='Nhà hàng B', owner_user_id=self.owner2.id,
                                      category_id=self.category.id, active=True, lat=10.0, lng=106.0)
        db.session.add_all([self.restaurant1, self.restaurant2])
        db.session.commit()

        self.dish1_res1 = Dish(name='Cơm sườn', price=30000, restaurant_id=self.restaurant1.id)
        self.dish1_res2 = Dish(name='Phở bò', price=50000, restaurant_id=self.restaurant2.id)
        db.session.add_all([self.dish1_res1, self.dish1_res2])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_add_to_cart_first_item(self):
        """Kiểm thử: Thêm món đầu tiên vào giỏ hàng trống."""
        response = self.client.post('/api/add-to-cart',
                                    json={'dish_id': self.dish1_res1.id, 'quantity': 2})

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])

        with self.client.session_transaction() as sess:
            cart = sess['cart']
            res_id_str = str(self.restaurant1.id)
            self.assertIn(res_id_str, cart)
            self.assertEqual(len(cart[res_id_str]['items']), 1)
            item_key = list(cart[res_id_str]['items'].keys())[0]
            self.assertEqual(cart[res_id_str]['items'][item_key]['quantity'], 2)

    def test_add_to_cart_from_multiple_restaurants(self):
        """Kiểm thử: Thêm món từ nhà hàng B KHÔNG xóa giỏ hàng của nhà hàng A."""
        self.client.post('/api/add-to-cart', json={'dish_id': self.dish1_res1.id})
        self.client.post('/api/add-to-cart', json={'dish_id': self.dish1_res2.id})

        with self.client.session_transaction() as sess:
            cart = sess['cart']
            self.assertIn(str(self.restaurant1.id), cart)
            self.assertIn(str(self.restaurant2.id), cart)
            self.assertEqual(len(cart), 2)

    def test_update_cart_item_quantity(self):
        """Kiểm thử: Cập nhật số lượng một món trong giỏ hàng."""
        add_response = self.client.post('/api/add-to-cart', json={'dish_id': self.dish1_res1.id, 'quantity': 1})
        cart_data = add_response.get_json()['cart']
        item_key = list(cart_data[str(self.restaurant1.id)]['items'].keys())[0] #thoongtin món ăn

        update_response = self.client.post('/api/update-cart-item',
                                           json={
                                               'restaurant_id': self.restaurant1.id,
                                               'item_key': item_key,
                                               'quantity': 5
                                           })
        self.assertEqual(update_response.status_code, 200)
        with self.client.session_transaction() as sess:
            self.assertEqual(sess['cart'][str(self.restaurant1.id)]['items'][item_key]['quantity'], 5)

    def test_checkout_requires_login(self):
        """Kiểm thử: Không thể vào trang checkout nếu chưa đăng nhập."""
        with self.client.session_transaction() as sess:
            sess['cart'] = {str(self.restaurant1.id): {'items': {'dish_1': {'quantity': 1, 'price': 1}}}}

        response = self.client.get(f'/checkout/{self.restaurant1.id}', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertTrue('/login' in response.location or url_for('main.login_view') in response.location)

    @patch('index.create_momo_payment_request')
    def test_successful_checkout(self, mock_create_momo_request):
        """Kiểm thử: Luồng đặt hàng MoMo thành công (sử dụng mock)."""
        mock_create_momo_request.return_value = 'https://test-payment.momo.vn/v2/gateway/pay'

        # 2. Đăng nhập
        self.client.post(url_for('main.login_view'), data={
            'phone': self.user1.phone,
            'password': self.user1_pass
        }, follow_redirects=True)

        # 3. Thêm món vào giỏ
        self.client.post('/api/add-to-cart',
                         json={'dish_id': self.dish1_res1.id, 'quantity': 2})

        # 4. Đặt hàng
        checkout_response = self.client.post(f'/checkout/{self.restaurant1.id}', data={
            'delivery_address': '123 Test Street',
            'note': 'Test note',
            'payment_method': 'momo',
            'discount_amount': 0,
            'voucher_ids': ''
        }, follow_redirects=False)

        # 5. Kiểm tra
        mock_create_momo_request.assert_called_once()
        # Response có đúng là chuyển hướng đến URL mà mock đã trả về không?
        self.assertEqual(checkout_response.status_code, 302)
        self.assertEqual(checkout_response.location, 'https://test-payment.momo.vn/v2/gateway/pay')

        # 6. Kiểm tra CSDL và session (giữ nguyên)
        orders = Order.query.filter_by(user_id=self.user1.id).all()
        self.assertEqual(len(orders), 1)