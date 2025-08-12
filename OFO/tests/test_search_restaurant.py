import unittest
# <<< DÒNG SỬA QUAN TRỌNG NHẤT LÀ ĐÂY >>>
from models import Restaurant, Category, User
from __init__ import create_app, db
from dao import search_and_classify_restaurants


class SearchRestaurantTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        self.owner = User(
            name='Chủ nhà hàng Test',
            email='owner@test.com',
            phone='0909090909',
            password='password'
        )
        db.session.add(self.owner)
        db.session.commit()

        # 2. Tạo Category
        self.cat_fast_food = Category(name='Đồ ăn nhanh')
        self.cat_healthy = Category(name='Đồ ăn lành mạnh')
        db.session.add_all([self.cat_fast_food, self.cat_healthy])
        db.session.commit()

        res1_kfc = Restaurant(
            restaurant_name='KFC Quận 1', active=True, category_id=self.cat_fast_food.id,
            lat=10.778, lng=106.701, owner_user_id=self.owner.id
        )
        res2_pizza_hut = Restaurant(
            restaurant_name='Pizza Hut Quận 3', active=True, category_id=self.cat_fast_food.id,
            lat=10.785, lng=106.695, owner_user_id=self.owner.id
        )
        res3_lotteria_q7 = Restaurant(
            restaurant_name='Lotteria Quận 7', active=True, category_id=self.cat_fast_food.id,
            lat=10.850, lng=106.770, owner_user_id=self.owner.id
        )
        res4_jollibee_bien_hoa = Restaurant(
            restaurant_name='Jollibee Biên Hòa', active=True, category_id=self.cat_fast_food.id,
            lat=10.950, lng=106.820, owner_user_id=self.owner.id
        )
        res5_mcdonald_inactive = Restaurant(
            restaurant_name='McDonalds Tạm nghỉ', active=False, category_id=self.cat_fast_food.id,
            lat=10.776, lng=106.700, owner_user_id=self.owner.id
        )

        db.session.add_all([res1_kfc, res2_pizza_hut, res3_lotteria_q7, res4_jollibee_bien_hoa, res5_mcdonald_inactive])
        db.session.commit()

        self.kfc_id = res1_kfc.id

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_search_without_location_data(self):
        """
        Kiểm thử tìm kiếm khi không cung cấp vị trí người dùng.
        """
        nearby, others = search_and_classify_restaurants(category_name='Đồ ăn nhanh')
        self.assertEqual(len(nearby), 0)
        self.assertEqual(len(others), 4)  # Sửa lại số lượng mong đợi vì có 4 nhà hàng active
        self.assertIsNone(others[0].distance_km)

    def test_search_with_location_and_classification(self):
        """
        Kiểm thử trường hợp chính: Tìm kiếm có vị trí và phân loại đúng.
        """
        user_lat = 10.7769
        user_lng = 106.7009
        nearby, others = search_and_classify_restaurants(
            category_name='Đồ ăn nhanh',
            user_lat=user_lat,
            user_lng=user_lng
        )
        self.assertEqual(len(nearby), 2)
        self.assertEqual(len(others), 2)
        nearby_names = [r.restaurant_name for r in nearby]
        self.assertIn('KFC Quận 1', nearby_names)
        self.assertIn('Pizza Hut Quận 3', nearby_names)
        self.assertEqual(nearby[0].restaurant_name, 'KFC Quận 1')

    def test_search_with_nonexistent_category(self):
        """
        Kiểm thử tìm kiếm với một danh mục không tồn tại.
        """
        nearby, others = search_and_classify_restaurants(category_name='Đồ ăn chay')
        self.assertEqual(len(nearby), 0)
        self.assertEqual(len(others), 0)

    def test_search_when_all_restaurants_are_inactive(self):
        """
        Kiểm thử khi nhà hàng khớp danh mục nhưng không hoạt động.
        """
        Restaurant.query.update({Restaurant.active: False})
        db.session.commit()
        nearby, others = search_and_classify_restaurants(category_name='Đồ ăn nhanh')
        self.assertEqual(len(nearby), 0)
        self.assertEqual(len(others), 0)

if __name__ == '__main__':
    unittest.main()