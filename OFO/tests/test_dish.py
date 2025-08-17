# OFO/tests/test_dao.py

import unittest
from __init__ import create_app, db
# Giả sử các model của bạn ở OFO.models
from models import Dish, Restaurant, DishGroup, DishOptionGroup,User,UserRole
# Import hàm cần test
from dao import add_dish, delete_dish,get_dish_details_for_edit,update_dish_with_options
from werkzeug.datastructures import ImmutableMultiDict

class DishTestCase(unittest.TestCase):
    def setUp(self):
        """Thiết lập môi trường test với đầy đủ dữ liệu cần thiết."""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Dựng "sân khấu"
        test_user = User(name="testowner", email="owner@test.com", password="password", role=UserRole.RESTAURANT)
        db.session.add(test_user)
        db.session.commit()

        restaurant1 = Restaurant(restaurant_name="Nhà hàng Test 1", owner_user_id=test_user.id)
        db.session.add(restaurant1)
        db.session.commit()

        dish_group1 = DishGroup(name="Món chính", restaurant_id=restaurant1.id)
        db.session.add(dish_group1)

        option_group1 = DishOptionGroup(name="Size", restaurant_id=restaurant1.id)
        option_group2 = DishOptionGroup(name="Thêm topping", restaurant_id=restaurant1.id)
        option_group3 = DishOptionGroup(name="Mức độ cay", restaurant_id=restaurant1.id)
        db.session.add_all([option_group1, option_group2, option_group3])

        # <<<<<<<<<<<<<<< PHẦN QUAN TRỌNG NHẤT BẮT ĐẦU TỪ ĐÂY >>>>>>>>>>>>>>>>
        # 1. TẠO RA MỘT BIẾN TÊN LÀ `dish_to_modify`
        # Đây là món ăn "vật thí nghiệm" sẽ được dùng trong các test Sửa, Xóa, Lấy chi tiết
        dish_to_modify = Dish(
            name="Phở Bò Tái", description="Phở bò truyền thống", price=50000.0,
            restaurant_id=restaurant1.id, dish_group_id=dish_group1.id
        )
        # Gắn sẵn 2 option group cho món ăn này
        dish_to_modify.option_groups.append(option_group1)
        dish_to_modify.option_groups.append(option_group2)
        db.session.add(dish_to_modify)
        # <<<<<<<<<<<<<<< KẾT THÚC PHẦN TẠO BIẾN >>>>>>>>>>>>>>>>

        db.session.commit()

        # Lưu lại các ID cần thiết để các hàm test có thể sử dụng
        self.restaurant_id = restaurant1.id
        self.dish_group_id = dish_group1.id
        # 2. BÂY GIỜ BẠN CÓ THỂ LẤY ID TỪ BIẾN `dish_to_modify` MÀ KHÔNG BỊ LỖI
        self.dish_to_modify_id = dish_to_modify.id
        self.option_group1_id = option_group1.id
        self.option_group2_id = option_group2.id
        self.option_group3_id = option_group3.id
    def tearDown(self):
        """Dọn dẹp "sân khấu" sau mỗi lần test."""
        # db.session.remove()
        # db.drop_all()
        self.app_context.pop()

    def test_add_dish_success_simple(self):
        """Kiểm tra trường hợp thêm món ăn thành công (không có tùy chọn)."""
        DISH_NAME_UNIQUE = "Bún Bò Huế"

        result = add_dish(
            name=DISH_NAME_UNIQUE,
            description="Bún bò cay nồng",
            price=55000.0,
            active=True,
            image_url="bunbo.jpg",
            dish_group_id=self.dish_group_id,
            restaurant_id=self.restaurant_id
        )

        # SỬA Ở ĐÂY: Tìm kiếm món ăn cũng bằng cái tên mới đó
        dish = Dish.query.filter_by(name=DISH_NAME_UNIQUE).first()

        self.assertTrue(result)
        self.assertIsNotNone(dish)
        self.assertEqual(len(dish.option_groups), 0)

    def test_add_dish_success_with_options(self):
        """Kiểm tra trường hợp thêm món ăn thành công với các nhóm tùy chọn."""
        option_ids = [self.option_group1_id, self.option_group2_id]
        result = add_dish(
            name="Trà sữa trân châu",
            description="Trà sữa Đài Loan",
            price=45000.0,
            active=True,
            image_url="trasua.jpg",
            dish_group_id=self.dish_group_id,
            restaurant_id=self.restaurant_id,
            option_group_ids=option_ids
        )
        self.assertTrue(result)
        dish = Dish.query.filter_by(name="Trà sữa trân châu").first()
        self.assertIsNotNone(dish)
        self.assertEqual(len(dish.option_groups), 2)
        assigned_option_names = {og.name for og in dish.option_groups}
        self.assertIn("Size", assigned_option_names)

    def test_add_dish_with_invalid_option_id(self):
        """Kiểm tra việc thêm món ăn vẫn thành công khi có một ID tùy chọn không hợp lệ."""
        invalid_option_id = 999
        option_ids = [self.option_group1_id, invalid_option_id]
        result = add_dish(
            name="Cơm tấm sườn",
            description="Cơm tấm Sài Gòn",
            price=55000.0,
            active=True,
            image_url="comtam.jpg",
            dish_group_id=self.dish_group_id,
            restaurant_id=self.restaurant_id,
            option_group_ids=option_ids
        )
        self.assertTrue(result)
        dish = Dish.query.filter_by(name="Cơm tấm sườn").first()
        self.assertIsNotNone(dish)
        self.assertEqual(len(dish.option_groups), 1)
        self.assertEqual(dish.option_groups[0].id, self.option_group1_id)

    def test_add_dish_failure_due_to_invalid_foreign_key(self):
        """Kiểm tra thêm món ăn thất bại do restaurant_id không tồn tại."""
        invalid_restaurant_id = 999
        result = add_dish(
            name="Món ăn ma",
            description="Món này không nên tồn tại",
            price=10000.0,
            active=True,
            image_url="ghost.jpg",
            dish_group_id=self.dish_group_id,
            restaurant_id=invalid_restaurant_id
        )
        self.assertFalse(result)
        dish = Dish.query.filter_by(name="Món ăn ma").first()
        self.assertIsNone(dish)
        # =================================================================
        # ===== CÁC BÀI TEST CHO CHỨC NĂNG LẤY (GET) ======================
        # =================================================================

    def test_get_dish_details_success(self):
        """(LẤY) Kiểm tra lấy chi tiết món ăn thành công."""
        print(f"\n--- Mục đích: {self.test_get_dish_details_success.__doc__} ---")
        dish_data = get_dish_details_for_edit(self.dish_to_modify_id)

        self.assertIsNotNone(dish_data)
        self.assertEqual(dish_data['name'], "Phở Bò Tái")
        # Kiểm tra xem nó có lấy đúng danh sách ID của option group không
        self.assertCountEqual(dish_data['linked_option_group_ids'], [self.option_group1_id, self.option_group2_id])
        print(">>> Kết quả: ĐÚNG")

    def test_get_nonexistent_dish_details(self):
        """(LẤY) Kiểm tra lấy chi tiết món ăn không tồn tại."""
        print(f"\n--- Mục đích: {self.test_get_nonexistent_dish_details.__doc__} ---")
        dish_data = get_dish_details_for_edit(999)
        self.assertIsNone(dish_data)
        print(">>> Kết quả: ĐÚNG")

        # =================================================================
        # ===== CÁC BÀI TEST CHO CHỨC NĂNG SỬA (UPDATE) ===================
        # =================================================================

    def test_update_dish_with_options_success(self):
        """(SỬA) Kiểm tra cập nhật tên, giá và thay đổi nhóm tùy chọn thành công."""
        print(f"\n--- Mục đích: {self.test_update_dish_with_options_success.__doc__} ---")

        # Giả lập dữ liệu form gửi lên: đổi từ [Size, Topping] thành [Topping, Cay]
        mock_form_data = ImmutableMultiDict([
            ('dish_id', str(self.dish_to_modify_id)),
            ('name', 'Phở Tái Lăn Đặc Biệt'),
            ('description', 'Phở bò xào tái lăn'),
            ('price', '65000.0'),
            ('active', 'true'),
            ('dish_group_id', str(self.dish_group_id)),
            ('option_group_ids', str(self.option_group2_id)),  # Giữ lại Topping
            ('option_group_ids', str(self.option_group3_id)),  # Thêm Mức độ cay
        ])

        is_success, message = update_dish_with_options(mock_form_data)

        self.assertTrue(is_success)

        # Lấy lại món ăn từ DB để kiểm tra
        updated_dish = db.session.get(Dish, self.dish_to_modify_id)
        self.assertEqual(updated_dish.name, 'Phở Tái Lăn Đặc Biệt')
        self.assertEqual(updated_dish.price, 65000.0)

        # Kiểm tra các option group đã được cập nhật đúng
        linked_option_ids = {group.id for group in updated_dish.option_groups}
        self.assertCountEqual(linked_option_ids, {self.option_group2_id, self.option_group3_id})
        print(">>> Kết quả: ĐÚNG")

        # =================================================================
        # ===== CÁC BÀI TEST CHO CHỨC NĂNG XÓA (DELETE) ===================
        # =================================================================

    def test_delete_dish_success(self):
        """(XÓA) Kiểm tra xóa món ăn thành công."""
        print(f"\n--- Mục đích: {self.test_delete_dish_success.__doc__} ---")

        is_success, message = delete_dish(self.dish_to_modify_id)

        self.assertTrue(is_success)

        # Kiểm tra món ăn đã thực sự biến mất khỏi DB
        deleted_dish = db.session.get(Dish, self.dish_to_modify_id)
        self.assertIsNone(deleted_dish)
        print(">>> Kết quả: ĐÚNG")

    def test_delete_nonexistent_dish(self):
        """(XÓA) Kiểm tra xóa một món ăn không tồn tại."""
        print(f"\n--- Mục đích: {self.test_delete_nonexistent_dish.__doc__} ---")
        is_success, message = delete_dish(999)
        self.assertFalse(is_success)
        print(">>> Kết quả: ĐÚNG")

if __name__ == '__main__':
    unittest.main()