import json
import os
import config
import hashlib
from  models import *
from __init__ import db,app
import cloudinary.uploader
from sqlalchemy import func, event
from sqlalchemy.orm import subqueryload, joinedload

# Đăng nhập
def auth_user(phone, password):
    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())

    u = User.query.filter(User.phone.__eq__(phone),
                          User.password.__eq__(password))
    return u.first()

def get_user_by_id(user_id):
    return User.query.get(user_id)

def add_user(name,phone,email,password,avatar=None):
     password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
     u = User(name=name,phone=phone,email=email,password=password)
     if avatar:
         res = cloudinary.uploader.upload(avatar)
         u.avatar = res.get('secure_url')


     db.session.add(u)
     db.session.commit()

def load_categories(limit=8):
    """
    Hàm để tải tất cả các danh mục (Category) từ CSDL.
    """
    # Truy vấn và sắp xếp theo tên cho dễ nhìn
    query = Category.query.order_by(Category.name)
    if limit is not None:
        query = query.limit(limit)
    return query.all()

def load_random_restaurants(limit=10):
    """
    Lấy một danh sách nhà hàng ngẫu nhiên từ CSDL.
    Sử dụng func.random() cho SQLite/PostgreSQL hoặc func.rand() cho MySQL.
    """
    # Chỉnh func.rand() nếu bạn dùng MySQL, func.random() cho các DB khác
    query = Restaurant.query.order_by(func.random()).limit(limit)
    return query.all()

def get_restaurant_by_id(restaurant_id):
    """
    Lấy thông tin của một nhà hàng duy nhất bằng ID của nó.
    """
    # .get() là cách nhanh và hiệu quả nhất để truy vấn bằng khóa chính
    restaurant = Restaurant.query.options(
        # Dùng subqueryload để tải các DishGroup liên quan trong một query riêng
        subqueryload(Restaurant.dish_groups)
        # Từ các DishGroup đã tải, tiếp tục tải các Dish liên quan trong một query riêng nữa
        .subqueryload(DishGroup.dishes)
    ).get(restaurant_id)

    return restaurant

def get_dish_with_options(dish_id):
    """
    Lấy chi tiết một món ăn bao gồm các nhóm tùy chọn và tùy chọn con của nó.
    Sử dụng joinedload để tải trước tất cả dữ liệu liên quan trong một câu lệnh query.
    """
    dish = Dish.query.options(
        joinedload(Dish.option_groups).joinedload(DishOptionGroup.options)
    ).get(dish_id)

    return dish

def search_restaurants(category_name=None):
    """
    Tìm kiếm danh sách nhà hàng.
    Nếu có category_id, sẽ lọc theo danh mục đó.
    Nếu không, sẽ trả về tất cả nhà hàng.
    """
    query = Restaurant.query

    if category_name:
        # Join với bảng Category và lọc theo Category.name
        query = query.join(Category).filter(Category.name == category_name)

    return query.all()


def add_review(order_id, star, comment, image_urls=None):
    """
    Thêm một đánh giá mới vào CSDL, bao gồm cả các link ảnh.
    """
    order = Order.query.get(order_id)
    if not order:
        raise ValueError("Đơn hàng không tồn tại.")

    existing_review = Review.query.filter_by(order_id=order_id).first()
    if existing_review:
        raise ValueError("Đơn hàng này đã được đánh giá rồi.")

    # Nối danh sách các URL thành một chuỗi duy nhất, ngăn cách bằng dấu ';'
    image_string = None
    if image_urls and isinstance(image_urls, list):
        image_string = ";".join(image_urls)

    new_review = Review(
        user_id=order.user_id,
        restaurant_id=order.restaurant_id,
        order_id=order_id,
        star=star,
        comment=comment,
        image=image_string
    )

    db.session.add(new_review)
    db.session.commit()

    return new_review

@event.listens_for(Review, 'after_insert')
def receive_after_insert(mapper, connection, target):
    """
    Lắng nghe sự kiện sau khi một bản ghi Review được thêm vào.
    'target' chính là đối tượng Review vừa được tạo.
    """
    # Lấy restaurant_id từ review vừa được thêm
    restaurant_id = target.restaurant_id

    # Tính toán điểm trung bình
    # Lưu ý: chúng ta dùng connection.execute để chạy câu lệnh trong cùng một transaction
    avg_result = connection.execute(
        db.select(func.avg(Review.star)).where(Review.restaurant_id == restaurant_id)
    ).scalar_one_or_none()

    if avg_result is not None:
        average_rating = round(avg_result, 1)

        # Tạo câu lệnh UPDATE cho bảng Restaurant
        restaurant_table = Restaurant.__table__
        stmt = (
            restaurant_table.update()
            .where(restaurant_table.c.id == restaurant_id)
            .values(star_average=average_rating)
        )
        # Thực thi câu lệnh UPDATE
        connection.execute(stmt)

if __name__ == "__main__":
    print(auth_user("user", 123))