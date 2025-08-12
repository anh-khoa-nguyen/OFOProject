# tests/test_admin.py - PHIÊN BẢN CUỐI CÙNG

import unittest
import hashlib
from __init__ import create_app, db
from models import User, UserRole
from flask import url_for


class AdminPanelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        self.admin_pass_plain = 'adminpass'
        admin_pass_hashed = str(hashlib.md5(self.admin_pass_plain.encode('utf-8')).hexdigest())
        self.admin_user = User(name='Super Admin', email='admin@ofo.com', phone='0101010101',
                               password=admin_pass_hashed, role=UserRole.ADMIN, active=True)

        self.pending_restaurant_user = User(name='Quán Chờ Duyệt', email='pending@ofo.com', phone='0202020202',
                                            password='pass', role=UserRole.RESTAURANT, active=False)

        self.regular_user_pass_plain = 'userpass'
        self.regular_user = User(name='Khách Hàng A', email='user@ofo.com', phone='0404040404',
                                 password=str(hashlib.md5(self.regular_user_pass_plain.encode('utf-8')).hexdigest()),
                                 role=UserRole.USER, active=True)

        db.session.add_all([self.admin_user, self.pending_restaurant_user, self.regular_user])
        db.session.commit()

        self.client = self.app.test_client()
        self.client.post(
            url_for('main.login_view'),
            data={'phone': self.admin_user.phone, 'password': self.admin_pass_plain},
            follow_redirects=True
        )

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_admin_can_view_pending_restaurants(self):
        response = self.client.get('/admin/pending_users/')
        self.assertEqual(response.status_code, 200)
        # Sửa lại chuỗi tìm kiếm cho đúng
        response_text = response.data.decode('utf-8')
        self.assertIn('Quán Chờ Duyệt', response_text)
        self.assertNotIn(b'Super Admin', response.data)

    def test_admin_can_approve_pending_restaurant(self):
        response = self.client.post('/admin/pending_users/action/', data={
            'action': 'approve',
            'rowid': str(self.pending_restaurant_user.id)
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        response_text = response.data.decode('utf-8')
        self.assertIn('Đã duyệt 1 nhà hàng.', response_text)

        user_after = db.session.get(User, self.pending_restaurant_user.id)
        self.assertTrue(user_after.active)

    def test_regular_user_cannot_access_admin_panel(self):
        with self.app.test_client() as regular_client:
            regular_client.post(
                url_for('main.login_view'),
                data={'phone': self.regular_user.phone, 'password': self.regular_user_pass_plain},
                follow_redirects=True
            )
            response = regular_client.get('/admin/', follow_redirects=False)
            self.assertEqual(response.status_code, 302)
            self.assertTrue('/login' in response.location)  # Giả sử tên là reslogin