# OFO/tests/test_search.py

import unittest
from __init__ import create_app, db
from models import Restaurant, Category, User, UserRole
from dao import search_and_classify_restaurants

class SearchDaoTestCase(unittest.TestCase):
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

        # Tạo danh mục
        category_viet = Category(name="Đồ ăn Việt")
        category_fastfood = Category(name="Đồ ăn nhanh")
        db.session.add_all([category_viet, category_fastfood])
        db.session.commit()

        # Tọa độ người dùng cố định để test
        self.user_lat = 10.800000
        self.user_lng = 106.700000

        # Tạo các nhà hàng ở các khoảng cách và danh mục khác nhau
        # 1. Gần (< 10km), đúng danh mục
        res_nearby_correct_cat = Restaurant(restaurant_name="Quán Gần Đúng Loại", owner_user_id=test_user.id, category_id=category_viet.id, lat=10.83, lng=106.72) # ~4km
        # 2. Xa (> 10km, < 50km), đúng danh mục
        res_far_correct_cat = Restaurant(restaurant_name="Quán Xa Đúng Loại", owner_user_id=test_user.id, category_id=category_viet.id, lat=10.95, lng=106.80) # ~19km
        # 3. Rất xa (> 50km), đúng danh mục -> Sẽ bị loại
        res_very_far_correct_cat = Restaurant(restaurant_name="Quán Rất Xa", owner_user_id=test_user.id, category_id=category_viet.id, lat=11.50, lng=107.00) # ~80km
        # 4. Gần, nhưng sai danh mục -> Sẽ bị loại khi lọc theo category
        res_nearby_wrong_cat = Restaurant(restaurant_name="Quán Gần Sai Loại", owner_user_id=test_user.id, category_id=category_fastfood.id, lat=10.81, lng=106.71) # ~1.5km
        # 5. Đúng danh mục, nhưng không có tọa độ -> Sẽ bị loại khi có vị trí user
        res_no_coords_correct_cat = Restaurant(restaurant_name="Quán Không Tọa Độ", owner_user_id=test_user.id, category_id=category_viet.id)
        # 6. Một quán gần khác để kiểm tra sắp xếp
        res_nearby_correct_cat_2 = Restaurant(restaurant_name="Quán Gần Hơn Đúng Loại", owner_user_id=test_user.id, category_id=category_viet.id, lat=10.81, lng=106.71) # ~1.5km

        db.session.add_all([
            res_nearby_correct_cat, res_far_correct_cat, res_very_far_correct_cat,
            res_nearby_wrong_cat, res_no_coords_correct_cat, res_nearby_correct_cat_2
        ])
        db.session.commit()

    def tearDown(self):
        """Dọn dẹp "sân khấu" sau mỗi lần test."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    # =================================================================
    # ===== CÁC BÀI TEST CHO CHỨC NĂNG TÌM KIẾM & PHÂN LOẠI ==========
    # =================================================================

    def test_search_full_criteria_success(self):
        """(TÌM KIẾM) Kiểm tra tìm kiếm và phân loại thành công khi có đủ danh mục và vị trí."""
        print(f"\n--- Mục đích: {self.test_search_full_criteria_success.__doc__} ---")

        nearby, other = search_and_classify_restaurants(
            category_name="Đồ ăn Việt",
            user_lat=self.user_lat,
            user_lng=self.user_lng
        )

        # Kiểm tra danh sách "Gần"
        self.assertEqual(len(nearby), 2)
        nearby_names = {r.restaurant_name for r in nearby}
        self.assertIn("Quán Gần Đúng Loại", nearby_names)
        self.assertIn("Quán Gần Hơn Đúng Loại", nearby_names)

        # Kiểm tra danh sách "Có thể thích"
        self.assertEqual(len(other), 1)
        self.assertEqual(other[0].restaurant_name, "Quán Xa Đúng Loại")

        # Kiểm tra các quán bị loại
        all_returned_names = nearby_names.union({r.restaurant_name for r in other})
        self.assertNotIn("Quán Rất Xa", all_returned_names)
        self.assertNotIn("Quán Gần Sai Loại", all_returned_names)
        self.assertNotIn("Quán Không Tọa Độ", all_returned_names)

        # Kiểm tra sắp xếp
        self.assertLessEqual(nearby[0].distance_km, nearby[1].distance_km)
        self.assertEqual(nearby[0].restaurant_name, "Quán Gần Hơn Đúng Loại")

        print(">>> Kết quả: ĐÚNG - Phân loại và lọc nhà hàng chính xác.")


    def test_search_no_user_location(self):
        """(TÌM KIẾM) Kiểm tra tìm kiếm khi không có vị trí người dùng."""
        print(f"\n--- Mục đích: {self.test_search_no_user_location.__doc__} ---")
        nearby, other = search_and_classify_restaurants(category_name="Đồ ăn Việt")

        # Danh sách "Gần" phải rỗng
        self.assertEqual(len(nearby), 0)

        # Danh sách "other" chứa tất cả các nhà hàng thuộc danh mục "Đồ ăn Việt"
        self.assertEqual(len(other), 4)
        other_names = {r.restaurant_name for r in other}
        self.assertIn("Quán Gần Đúng Loại", other_names)
        self.assertIn("Quán Xa Đúng Loại", other_names)
        self.assertIn("Quán Rất Xa", other_names)
        self.assertIn("Quán Không Tọa Độ", other_names)

        # Khoảng cách và thời gian phải là None
        for r in other:
            self.assertIsNone(r.distance_km)
            self.assertIsNone(r.delivery_time_minutes)

        print(">>> Kết quả: ĐÚNG - Trả về tất cả nhà hàng phù hợp, không tính khoảng cách.")

    def test_search_no_category_filter(self):
        """(TÌM KIẾM) Kiểm tra tìm kiếm không lọc theo danh mục."""
        print(f"\n--- Mục đích: {self.test_search_no_category_filter.__doc__} ---")
        nearby, other = search_and_classify_restaurants(
            user_lat=self.user_lat,
            user_lng=self.user_lng
        )

        # Bây giờ quán "Sai Loại" cũng phải được tìm thấy
        self.assertEqual(len(nearby), 3)
        nearby_names = {r.restaurant_name for r in nearby}
        self.assertIn("Quán Gần Đúng Loại", nearby_names)
        self.assertIn("Quán Gần Hơn Đúng Loại", nearby_names)
        self.assertIn("Quán Gần Sai Loại", nearby_names) # Đã bao gồm quán sai loại

        self.assertEqual(len(other), 1)
        self.assertEqual(other[0].restaurant_name, "Quán Xa Đúng Loại")
        print(">>> Kết quả: ĐÚNG - Tìm thấy tất cả nhà hàng trong bán kính, không phân biệt danh mục.")

    def test_search_no_results_found(self):
        """(TÌM KIẾM) Kiểm tra trường hợp không tìm thấy nhà hàng nào."""
        print(f"\n--- Mục đích: {self.test_search_no_results_found.__doc__} ---")
        nearby, other = search_and_classify_restaurants(category_name="Đồ ăn Nhật")

        self.assertEqual(len(nearby), 0)
        self.assertEqual(len(other), 0)
        print(">>> Kết quả: ĐÚNG - Trả về hai danh sách rỗng khi không có kết quả.")

    def test_search_with_custom_radius(self):
        """(TÌM KIẾM) Kiểm tra tìm kiếm với bán kính tùy chỉnh."""
        print(f"\n--- Mục đích: {self.test_search_with_custom_radius.__doc__} ---")
        # Bán kính 3km sẽ chỉ bao gồm "Quán Gần Hơn" (~1.5km)
        nearby, other = search_and_classify_restaurants(
            category_name="Đồ ăn Việt",
            user_lat=self.user_lat,
            user_lng=self.user_lng,
            radius_km=3
        )

        self.assertEqual(len(nearby), 1)
        self.assertEqual(nearby[0].restaurant_name, "Quán Gần Hơn Đúng Loại")

        # "Quán Gần" (~4km) bây giờ sẽ nằm trong danh sách "other"
        self.assertEqual(len(other), 2)
        other_names = {r.restaurant_name for r in other}
        self.assertIn("Quán Gần Đúng Loại", other_names)
        self.assertIn("Quán Xa Đúng Loại", other_names)
        print(">>> Kết quả: ĐÚNG - Phân loại chính xác theo bán kính tùy chỉnh.")

if __name__ == '__main__':
    unittest.main()