# OFO/tests/test_voucher.py

import unittest
import datetime
from __init__ import create_app, db
# Import đầy đủ các model cần thiết
from models import Voucher, Restaurant, User, UserRole
# Import tất cả các hàm DAO cần test
from dao import add_voucher, update_voucher, delete_voucher, get_voucher_by_id


# Lưu ý: Các hàm update/delete của bạn dùng get_voucher_by_id.
# Nếu chưa có, hãy thêm nó vào dao.py:
# def get_voucher_by_id(voucher_id):
#     return db.session.get(Voucher, voucher_id)

class VoucherDaoTestCase(unittest.TestCase):
    def setUp(self):
        """Thiết lập môi trường test."""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # --- Dựng "sân khấu" ---
        test_user = User(name="testowner", email="owner@test.com", password="password", role=UserRole.RESTAURANT)
        db.session.add(test_user)
        db.session.commit()

        restaurant1 = Restaurant(restaurant_name="Nhà hàng Test 1", owner_user_id=test_user.id)
        db.session.add(restaurant1)
        db.session.commit()

        # Tạo sẵn một Voucher để dùng cho việc test Sửa và Xóa
        now = datetime.datetime.now()
        voucher_to_modify = Voucher(
            code="SALE50",
            name="Giảm giá 50%",
            percent=50.0,
            start_date=now,
            end_date=now + datetime.timedelta(days=30),
            restaurant_id=restaurant1.id
        )
        db.session.add(voucher_to_modify)
        db.session.commit()

        # Lưu lại các ID cần thiết
        self.restaurant_id = restaurant1.id
        self.voucher_to_modify_id = voucher_to_modify.id

    def tearDown(self):
        """Dọn dẹp sau mỗi test."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_add_voucher_success(self):
        """(THÊM) Kiểm tra thêm khuyến mãi mới thành công."""
        now = datetime.datetime.now()
        new_voucher_data = {
            "code": "FREESHIP",
            "name": "Miễn phí vận chuyển",
            "description": "Áp dụng cho mọi đơn hàng",
            "start_date": now,
            "end_date": now + datetime.timedelta(days=15),
            "restaurant_id": self.restaurant_id
        }

        created_voucher = add_voucher(new_voucher_data)

        self.assertIsNotNone(created_voucher)
        self.assertIsInstance(created_voucher, Voucher)
        self.assertEqual(created_voucher.code, "FREESHIP")

    def test_update_voucher_success(self):
        """(SỬA) Kiểm tra cập nhật mã và phần trăm khuyến mãi thành công."""
        update_data = {
            "code": "SALE70",
            "percent": 70.0
        }

        updated_voucher = update_voucher(self.voucher_to_modify_id, update_data)

        self.assertIsNotNone(updated_voucher)
        self.assertEqual(updated_voucher.code, "SALE70")
        self.assertEqual(updated_voucher.percent, 70.0)
        self.assertEqual(updated_voucher.name, "Giảm giá 50%")

    def test_update_nonexistent_voucher(self):
        """(SỬA) Kiểm tra cập nhật một khuyến mãi không tồn tại."""
        result = update_voucher(999, {"code": "FAKECODE"})
        self.assertIsNone(result)


    def test_delete_voucher_success(self):
        """(XÓA) Kiểm tra xóa khuyến mãi thành công."""
        result = delete_voucher(self.voucher_to_modify_id)

        self.assertTrue(result)

        deleted_voucher = get_voucher_by_id(self.voucher_to_modify_id)
        self.assertIsNone(deleted_voucher)

    def test_delete_nonexistent_voucher(self):
        """(XÓA) Kiểm tra xóa một khuyến mãi không tồn tại."""
        result = delete_voucher(999)
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()