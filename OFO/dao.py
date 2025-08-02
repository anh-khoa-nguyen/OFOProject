import json
import os
from sqlalchemy import func, event, text, desc

from sqlalchemy.exc import SQLAlchemyError

import config
import hashlib
from  models import *
from __init__ import db, app
import cloudinary.uploader
from sqlalchemy import func, event, text
from sqlalchemy.orm import subqueryload, joinedload
from geopy.distance import geodesic
from flask import request, jsonify
from zoneinfo import ZoneInfo
import random
import traceback
from __init__ import socketio
from sqlalchemy import inspect
from sqlalchemy import event

def get_greeting():
    """Lấy lời chào (sáng, trưa, chiều, tối) theo giờ Việt Nam."""
    hour = datetime.datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).hour
    if 5 <= hour < 11:
        return "buổi sáng"
    elif 11 <= hour < 14:
        return "buổi trưa"
    elif 14 <= hour < 18:
        return "buổi chiều"
    else:
        return "buổi tối"

def get_random_slogan():
    """
    Đọc file JSON và lấy một câu slogan chào mừng ngẫu nhiên.
    """
    # Tạo đường dẫn tuyệt đối đến file JSON
    file_path = os.path.join(app.static_folder, 'json', 'greeting_content.json')
    try:
        # Mở và đọc file với encoding utf-8 để hỗ trợ tiếng Việt
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            slogans = data.get("greetings", [])
            if slogans:
                return random.choice(slogans)
    except Exception as e:
        print(f"Lỗi khi đọc file greeting: {e}")

    # Trả về một câu mặc định nếu có lỗi xảy ra
    return "Bạn ơi, bạn đang ở đâu zậy?"

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
def get_restaurant_by_user_id(user_id):
    return Restaurant.query.filter_by(owner_user_id=user_id).first()


def load_categories(limit=8):
    """
    Hàm để tải tất cả các danh mục (Category) từ CSDL.
    """
    # Truy vấn và sắp xếp theo tên cho dễ nhìn
    query = Category.query.order_by(Category.name)
    if limit is not None:
        query = query.limit(limit)
    return query.all()


def _distance_and_time(restaurants, user_lat, user_lng):
    """
    Hàm phụ trợ: Nhận vào một danh sách nhà hàng và tọa độ người dùng,
    tính toán và thêm thuộc tính .distance_km và .delivery_time_minutes.
    """
    # Chỉ thực hiện nếu có đầy đủ thông tin
    if not all([restaurants, user_lat is not None, user_lng is not None]):
        return restaurants  # Trả về danh sách gốc nếu thiếu thông tin

    try:
        user_location = (float(user_lat), float(user_lng))
        for restaurant in restaurants:
            restaurant.distance_km = None
            restaurant.delivery_time_minutes = None  # Đổi tên cho rõ ràng

            if restaurant.lat and restaurant.lng:
                restaurant_location = (float(restaurant.lat), float(restaurant.lng))
                distance = geodesic(user_location, restaurant_location).km
                restaurant.distance_km = round(distance, 1)
                restaurant.delivery_time_minutes = round(10 + (distance * 5))
    except (ValueError, TypeError) as e:
        print(f"Lỗi khi xử lý tọa độ: {e}. Bỏ qua tính toán.")

    return restaurants

def load_random_restaurants(limit=10, user_lat=None, user_lng=None):
    """
    Lấy danh sách nhà hàng ngẫu nhiên.
    Nếu tọa độ người dùng được cung cấp, tính toán và thêm khoảng cách (distance_km)
    vào mỗi đối tượng nhà hàng.
    """
    # Lấy danh sách nhà hàng ngẫu nhiên từ CSDL
    restaurants = Restaurant.query.order_by(func.random()).limit(limit).all()

    # Chỉ tính khoảng cách nếu có tọa độ của người dùng
    if user_lat is not None and user_lng is not None:
        user_location = (user_lat, user_lng)

        for restaurant in restaurants:
            # Thêm thuộc tính mới để lưu thời gian giao hàng
            restaurant.distance_km = None
            restaurant.delivery_time = None

            if restaurant.lat and restaurant.lng:
                restaurant_location = (float(restaurant.lat), float(restaurant.lng))

                # Tính khoảng cách
                distance = geodesic(user_location, restaurant_location).km
                restaurant.distance_km = round(distance, 1)

                # ===================================================================
                # ÁP DỤNG CÔNG THỨC TÍNH THỜI GIAN GIAO HÀNG
                # Công thức: 10 phút (lấy hàng) + (số km * 5 phút)
                # ===================================================================
                pickup_time = 10
                time_per_km = 5
                estimated_time = pickup_time + (restaurant.distance_km * time_per_km)

                # Làm tròn đến số nguyên gần nhất và gán vào thuộc tính mới
                restaurant.delivery_time = round(estimated_time)

    return restaurants

def get_top_rated_restaurants(limit=10):
    """
    Lấy danh sách các nhà hàng được đánh giá cao nhất.
    Tiêu chí:
    1. Đang hoạt động (active=True).
    2. Điểm trung bình từ 4.6 trở lên.
    3. Sắp xếp theo số lượng đánh giá giảm dần.
    4. Giới hạn ở top 10.
    """
    # Câu query này sẽ join Restaurant với Review, đếm số review,
    # sau đó lọc và sắp xếp.
    top_restaurants_query = db.session.query(
        Restaurant,
        func.count(Review.id).label('review_count')
    ).outerjoin(Review, Restaurant.id == Review.restaurant_id) \
        .filter(Restaurant.active == True) \
        .filter(Restaurant.star_average >= 4.6) \
        .group_by(Restaurant.id) \
        .order_by(func.count(Review.id).desc()) \
        .limit(limit)

    # Query trên trả về một danh sách các tuple (Restaurant, review_count).
    # Chúng ta chỉ cần lấy đối tượng Restaurant.
    restaurants = [restaurant for restaurant, count in top_restaurants_query.all()]

    return restaurants

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


def search_and_classify_restaurants(category_name=None, user_lat=None, user_lng=None, radius_km=10):
    """
    Tìm kiếm và phân loại nhà hàng thành hai nhóm:
    1. Gần: <= 10km
    2. Có thể thích: > 10km và <= 50km
    """
    query = Restaurant.query.filter_by(active=True)

    if category_name:
        query = query.join(Restaurant.category).filter(Category.name == category_name)

    all_restaurants = query.all()

    if user_lat is None or user_lng is None:
        for r in all_restaurants:
            r.distance_km = None
            r.delivery_time_minutes = None
        return [], all_restaurants

    user_location = (float(user_lat), float(user_lng))
    nearby_restaurants = []
    other_restaurants = []

    for restaurant in all_restaurants:
        if not (restaurant.lat and restaurant.lng):
            continue

        restaurant_location = (float(restaurant.lat), float(restaurant.lng))
        distance = geodesic(user_location, restaurant_location).km


        restaurant.distance_km = round(distance, 2)
        restaurant.delivery_time_minutes = round(10 + (distance * 5))

        if distance <= radius_km:
            nearby_restaurants.append(restaurant)
        # 2. Nếu không, kiểm tra xem có trong bán kính "xa" hay không (> 10km và <= 50km)
        elif distance <= 50:
            other_restaurants.append(restaurant)
        # Các nhà hàng có distance > 50km sẽ không được thêm vào danh sách

    # Sắp xếp danh sách nhà hàng ở xa theo khoảng cách tăng dần
    other_restaurants.sort(key=lambda r: r.distance_km)
    nearby_restaurants.sort(key=lambda r: r.distance_km)

    return nearby_restaurants, other_restaurants

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
    # Lấy restaurant_id từ review.css vừa được thêm
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

def get_reviews_by_restaurant(restaurant_id):
    """
    Lấy tất cả các đánh giá cho một nhà hàng cụ thể, sắp xếp từ mới nhất đến cũ nhất.
    """
    # .options(joinedload(Review.user)) sẽ tải trước thông tin người dùng để tránh N+1 query
    return Review.query.filter_by(restaurant_id=restaurant_id)\
                       .order_by(Review.date.desc())\
                       .all()


def get_restaurant_review_summary(restaurant_id):
    """
    Lấy dữ liệu tổng hợp về đánh giá cho một nhà hàng.
    Bao gồm: tổng số review và số lượng cho từng mức sao.
    """
    # Dùng một câu query duy nhất để lấy số lượng cho từng mức sao
    breakdown_query = db.session.query(
        Review.star,
        func.count(Review.id)
    ).filter(Review.restaurant_id == restaurant_id).group_by(Review.star).all()

    # Chuyển kết quả thành một dictionary, ví dụ: {5: 10, 4: 5, ...}
    # Đồng thời tính tổng số review
    total_reviews = 0
    breakdown_dict = {star: 0 for star in range(1, 6)}  # Khởi tạo với tất cả giá trị = 0

    for star, count in breakdown_query:
        breakdown_dict[star] = count
        total_reviews += count

    return {
        'total_reviews': total_reviews,
        'breakdown': breakdown_dict
    }

def is_favorite(user_id, restaurant_id):
    """
    Kiểm tra xem một nhà hàng đã được người dùng yêu thích hay chưa.
    """
    user = User.query.get(user_id)
    if user:
        # .any() là cách hiệu quả để kiểm tra sự tồn tại
        return user.favorite_restaurants.filter(Restaurant.id == restaurant_id).first() is not None
    return False
#Load restaurant_main:
def get_dish_groups_by_restaurant(restaurant_id):
    return DishGroup.query.filter_by(restaurant_id=restaurant_id).all()
def get_dish_option_groups_by_restaurant(restaurant_id):
    return DishOptionGroup.query.filter_by(restaurant_id=restaurant_id).order_by(DishOptionGroup.name).all()
def update_option_group_with_options(data):
        group_id = data.get('id')
        if not group_id:
            return False, "Thiếu ID của nhóm cần cập nhật."
        try:
            with db.session.begin_nested():
                # 1. Tìm đối tượng cần sửa trong database
                group_to_update = db.session.query(DishOptionGroup).get(group_id)
                if not group_to_update:
                    return False, f"Không tìm thấy nhóm tùy chọn với ID {group_id}."
                # 2. Cập nhật các thuộc tính của nhóm cha
                group_to_update.name = data.get('name', '').strip()
                group_to_update.max = data.get('max')
                group_to_update.mandatory = data.get('mandatory', False)
                # Xóa các option cũ khỏi session
                for option in list(group_to_update.options):
                    db.session.delete(option)

                # Thêm các option mới từ payload vào session
                new_options_data = data.get('options', [])
                for option_data in new_options_data:
                    if option_data.get('name'):  # Chỉ thêm nếu có tên
                        new_option = DishOption(
                            name=option_data.get('name').strip(),
                            price=option_data.get('price', 0)
                        )
                        group_to_update.options.append(new_option)
            db.session.commit()
            return True, group_to_update
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"LỖI DATABASE KHI CẬP NHẬT NHÓM TÙY CHỌN (DAO): {e}")
            return False, "Lỗi cơ sở dữ liệu khi cập nhật."
        except Exception as e:
            db.session.rollback()
            print(f"LỖI KHÔNG MONG MUỐN KHI CẬP NHẬT NHÓM TÙY CHỌN (DAO): {e}")
            return False, "Có lỗi không mong muốn xảy ra."
def add_option_group_with_options(data):

    try:
        new_group = DishOptionGroup(
            restaurant_id=data.get('restaurant_id'),
            name=data.get('name'),
            mandatory=data.get('mandatory', False),
            max=data.get('max')
        )
        options_data = data.get('options', [])
        if not options_data:
            raise ValueError("Nhóm tùy chọn phải có ít nhất một lựa chọn.")

        for option_data in options_data:
            new_option = DishOption(
                name=option_data.get('name'),
                price=option_data.get('price', 0)
            )
            new_group.options.append(new_option)

        db.session.add(new_group)
        db.session.commit()
        return new_group
    except (SQLAlchemyError, ValueError) as e:
        # Nếu có bất kỳ lỗi nào, hủy bỏ mọi thay đổi
        print(f"ERROR - Could not add option group: {e}")
        db.session.rollback()
        return None


def delete_option_group_by_id(group_id):
    try:
        __tablename__ = 'dish_option_group'
        group_to_delete = db.session.query(DishOptionGroup).get(group_id)
        if not group_to_delete:
            return False, f"Không tìm thấy nhóm tùy chọn với ID {group_id}."
        group_name = group_to_delete.name
        db.session.delete(group_to_delete)
        db.session.commit()
        return True, f'Đã xóa thành công nhóm "{group_name}".'
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"LỖI DATABASE KHI XÓA NHÓM TÙY CHỌN (DAO): {e}")
        return False, "Lỗi cơ sở dữ liệu khi xóa."
    except Exception as e:
        db.session.rollback()
        print(f"LỖI KHÔNG MONG MUỐN KHI XÓA NHÓM TÙY CHỌN (DAO): {e}")
        return False, "Có lỗi không mong muốn xảy ra."

def add_dishgroup(name, restaurant_id):

    if DishGroup.query.filter(
        DishGroup.restaurant_id == restaurant_id,
        func.lower(DishGroup.name) == name.lower()
    ).first():
        return {'success': False, 'message': 'Tên nhóm món này đã tồn tại.'}

    try:
        new_group = DishGroup(name=name.strip(), restaurant_id=restaurant_id)
        db.session.add(new_group)
        db.session.commit()

        return {
            'success': True,
            'message': 'Thêm nhóm món thành công!',
            'group': {
                'id': new_group.id,
                'name': new_group.name
            }
        }
    except Exception as e:
        db.session.rollback() # Rất quan trọng: Hủy bỏ thay đổi nếu có lỗi
        print(f"LỖI KHI THÊM NHÓM MÓN: {e}")
        return {'success': False, 'message': 'Có lỗi xảy ra, không thể thêm nhóm món.'}


def delete_dishgroup_by_id(group_id):
    group = DishGroup.query.get(group_id)

    if group:
        try:
            for dish in group.dishes:
                db.session.delete(dish)
            db.session.delete(group)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()  # Hủy bỏ nếu có lỗi
            print(f"LỖI KHI XÓA NHÓM MÓN VÀ CÁC MÓN ĂN: {e}")
            return False

    return False
def add_dish(name, description, price, image_url, dish_group_id, restaurant_id,option_group_ids=None):
    try:
        dish = Dish(
            name=name,
            description=description,
            price=price,
            image=image_url,
            dish_group_id=dish_group_id,
            restaurant_id=restaurant_id
        )
        if option_group_ids:
            # Lặp qua từng ID trong danh sách được gửi lên
            for group_id in option_group_ids:
                # Tìm đối tượng DishOptionGroup tương ứng trong database
                group = DishOptionGroup.query.get(int(group_id))

                # Nếu tìm thấy, thêm nó vào mối quan hệ của món ăn mới.
                # SQLAlchemy sẽ tự động tạo bản ghi trong bảng trung gian `dish_has_option_groups`.
                if group:
                    dish.option_groups.append(group)

        db.session.add(dish)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print("❌ Lỗi khi thêm món ăn trong DAO:", e)
        return False


def get_dish_details_for_edit(dish_id):
    """
    Lấy thông tin chi tiết của một món ăn để điền vào form sửa.
    Bao gồm cả danh sách ID của các nhóm tùy chọn đã được liên kết.
    """
    try:
        dish = Dish.query.get(dish_id)
        if not dish:
            return None

        # Tạo một dictionary để chứa dữ liệu trả về
        dish_data = {
            "id": dish.id,
            "name": dish.name,
            "description": dish.description,
            "price": dish.price,
            "dish_group_id": dish.dish_group_id,
            # Dùng list comprehension để lấy danh sách ID của các nhóm đã liên kết
            "linked_option_group_ids": [group.id for group in dish.option_groups]
        }
        return dish_data
    except Exception as e:
        print(f"❌ Lỗi khi lấy chi tiết món ăn (DAO): {e}")
        return None


def update_dish_with_options(form_data, image_file=None):
    """
    Cập nhật thông tin một món ăn, bao gồm cả hình ảnh và các liên kết nhiều-nhiều.
    Đã tích hợp logic upload ảnh từ hàm update_dish cũ.

    Args:
        form_data (werkzeug.datastructures.ImmutableMultiDict): Dữ liệu từ request.form.
        image_file (FileStorage, optional): File ảnh từ request.files. Defaults to None.

    Returns:
        tuple: (True, "Success message") hoặc (False, "Error message")
    """
    dish_id = form_data.get('dish_id')
    if not dish_id:
        return False, "Thiếu ID của món ăn cần cập nhật."

    try:
        # 1. Tìm món ăn cần cập nhật
        dish_to_update = Dish.query.get(int(dish_id))
        if not dish_to_update:
            return False, "Không tìm thấy món ăn."

        # 2. Cập nhật các trường thông tin cơ bản (lấy từ hàm cũ của bạn)
        dish_to_update.name = form_data.get('name', '').strip()
        dish_to_update.description = form_data.get('description', '').strip()
        dish_to_update.price = float(form_data.get('price'))
        dish_to_update.dish_group_id = int(form_data.get('dish_group_id'))
        # restaurant_id thường không đổi, nhưng vẫn có thể cập nhật nếu cần
        # dish_to_update.restaurant_id = int(form_data.get('restaurant_id'))

        # 3. XỬ LÝ UPLOAD ẢNH MỚI (LOGIC TỪ HÀM CŨ CỦA BẠN)
        # Nếu người dùng có tải lên file ảnh mới
        if image_file and image_file.filename != '':
            # Lấy đường dẫn tuyệt đối đến thư mục static để đảm bảo an toàn
            upload_dir = os.path.join(app.root_path, 'static/image')
            os.makedirs(upload_dir, exist_ok=True)

            # Lưu file vào thư mục
            filename = image_file.filename
            save_path = os.path.join(upload_dir, filename)
            image_file.save(save_path)

            # Cập nhật đường dẫn ảnh mới vào database
            dish_to_update.image = f'image/{filename}'

        # 4. Cập nhật các liên kết với nhóm tùy chọn (logic mới)
        new_option_group_ids = form_data.getlist('option_group_ids')
        dish_to_update.option_groups.clear()  # Xóa hết liên kết cũ
        if new_option_group_ids:
            for group_id in new_option_group_ids:
                group = DishOptionGroup.query.get(int(group_id))
                if group:
                    dish_to_update.option_groups.append(group)

        # 5. Lưu tất cả thay đổi vào database
        db.session.commit()
        return True, "Cập nhật món ăn thành công!"

    except Exception as e:
        db.session.rollback()
        print(f"❌ Lỗi khi cập nhật món ăn (DAO): {e}")
        return False, str(e)  # Trả về lỗi cụ thể


def delete_dish(dish_id):
    try:
        dish = Dish.query.get(dish_id)
        if not dish:
            return False, "Món ăn không tồn tại"
        db.session.delete(dish)
        db.session.commit()
        return True, None
    except Exception as e:
        db.session.rollback()
        return False, str(e)

#ĐĂNG KÍ NHÀ HÀNG
def get_categories():
    try:
        return Category.query.all()
    except Exception as e:
        print(f"Lỗi khi lấy danh sách category: {e}")
        return []


def register_restaurant_and_user(username, email, password, phone, res_name, address,
                                 description, open_time, close_time, category_id,
                                 avatar_url=None, cover_url=None):

    if User.query.filter_by(email=email.strip()).first():
        return (False, 'Email này đã được sử dụng cho một tài khoản khác.')
    if User.query.filter_by(phone=phone.strip()).first():
        return (False, 'Số điện thoại này đã được đăng ký.')
    try:
        hashed_password = hashlib.md5(password.encode('utf-8')).hexdigest()

        new_user = User(
            name=username.strip(),
            email=email.strip(),
            password=hashed_password,
            phone=phone.strip(),
            avatar=avatar_url,
            role=UserRole.RESTAURANT
        )
        open_t = datetime.datetime.strptime(open_time, '%H:%M').time()
        close_t = datetime.datetime.strptime(close_time, '%H:%M').time()
        new_restaurant = Restaurant(
            restaurant_name=res_name,
            address=address,
            description=description,
            open_time=open_t,
            close_time=close_t,
            image=cover_url,
            category_id=int(category_id)
        )

        new_restaurant.user = new_user
        db.session.add(new_user)
        db.session.add(new_restaurant)

        db.session.commit()
        return (True, new_user)

    except Exception as e:
        db.session.rollback()
        print("‼️ ERROR TRONG DAO:", e)
        traceback.print_exc()
        return (False, 'Đã có lỗi xảy ra trong quá trình xử lý dữ liệu.')

def get_category_by_name(name):
    return Category.query.filter(Category.name.ilike(f"%{name}%")).first()
def toggle_favorite(user_id, restaurant_id):
    user = User.query.get(user_id)
    restaurant = Restaurant.query.get(restaurant_id)

    if not user or not restaurant:
        raise ValueError("Người dùng hoặc nhà hàng không tồn tại.")

    if restaurant in user.favorite_restaurants:
        # Nếu đã có, thì xóa đi
        user.favorite_restaurants.remove(restaurant)
        db.session.commit()
        return 'removed'
    else:
        # Nếu chưa có, thì thêm vào
        user.favorite_restaurants.append(restaurant)
        db.session.commit()
        return 'added'


def get_dish_by_id(dish_id):
    try:
        return db.session.get(Dish, int(dish_id))
    except (ValueError, TypeError):
        return None


def get_options_by_ids(option_ids):
    if not option_ids:
        return []
    try:
        int_option_ids = [int(opt_id) for opt_id in option_ids]

        # Sử dụng filter và .in_() để truy vấn hiệu quả nhiều ID cùng lúc
        return DishOption.query.filter(DishOption.id.in_(int_option_ids)).all()
    except (ValueError, TypeError):
        return []
def get_dish_details_by_id(dish_id):
    """
    Lấy thông tin chi tiết của một món ăn, bao gồm cả các nhóm tùy chọn
    và các tùy chọn con của nó.
    """
    try:
        dish = db.session.get(Dish, int(dish_id))
        if not dish:
            return None

        dish_data = {
            "id": dish.id,
            "name": dish.name,
            "description": dish.description,
            "price": dish.price,
            "image": dish.image,
            "option_groups": []
        }

        # Lấy các nhóm tùy chọn được liên kết với món ăn này
        for group in dish.option_groups:
            group_data = {
                "id": group.id,
                "name": group.name,
                "mandatory": group.mandatory,
                "max_selection": group.max,
                "options": []
            }
            for option in group.options:
                option_data = {
                    "id": option.id,
                    "name": option.name,
                    "price_change": option.price
                }
                group_data["options"].append(option_data)
            dish_data["option_groups"].append(group_data)

        return dish_data
    except (ValueError, TypeError):
        return None

# 3.3.6 Module Lịch sử và chi tiết đơn hàng, nhà hàng yêu thích
def get_orders_by_user_id(user_id):
    """
    Lấy danh sách các đơn hàng của một người dùng, sắp xếp theo ngày đặt mới nhất.
    Tải sẵn thông tin nhà hàng và chi tiết đơn hàng để tối ưu.
    """
    return db.session.query(Order).options(
        joinedload(Order.restaurant),
        joinedload(Order.details).joinedload(OrderDetail.dish)
    ).filter(Order.user_id == user_id).order_by(Order.order_date.desc()).all()

def get_order_details_by_id(order_id):
    try:
        order = db.session.query(Order).options(
            joinedload(Order.details).joinedload(OrderDetail.dish),
            joinedload(Order.restaurant),
            joinedload(Order.user)
        ).filter(Order.id == order_id).one_or_none()

        return order
    except Exception as e:
        print(f"Đã xảy ra lỗi khi lấy chi tiết đơn hàng: {e}")
        return None

#Xử lý thanh toán và voucher
def get_valid_vouchers(restaurant_id, subtotal):
    """
    Lấy danh sách các voucher đang hoạt động của một nhà hàng
    mà đơn hàng hiện tại đủ điều kiện áp dụng.
    """
    now = datetime.datetime.now()
    return Voucher.query.filter(
        Voucher.restaurant_id == restaurant_id,
        Voucher.active == True,
        Voucher.start_date <= now,
        Voucher.end_date >= now,
        Voucher.min <= subtotal
    ).all()


def apply_voucher(code, restaurant_id, subtotal):
    """
    Kiểm tra một mã voucher và tính toán số tiền được giảm.
    """
    now = datetime.datetime.now()
    voucher = Voucher.query.filter(
        Voucher.code == code.upper(),  # Chuyển mã về chữ hoa để khớp
        Voucher.restaurant_id == restaurant_id,
        Voucher.active == True,
        Voucher.start_date <= now,
        Voucher.end_date >= now
    ).first()

    if not voucher:
        return {'success': False, 'message': 'Mã khuyến mãi không hợp lệ hoặc đã hết hạn.'}

    if subtotal < voucher.min:
        return {'success': False, 'message': f'Đơn hàng cần tối thiểu {voucher.min:,.0f}đ để áp dụng mã này.'}

    # Tính toán giảm giá
    discount = 0
    if voucher.percent and voucher.percent > 0:
        discount = subtotal * (voucher.percent / 100)
        if voucher.max and discount > voucher.max:
            discount = voucher.max
    elif voucher.limit:
        discount = voucher.limit

    return {
        'success': True,
        'discount': discount,
        'voucher_id': voucher.id,
        'message': f'Áp dụng thành công mã "{voucher.name}"!'
    }


def create_order_from_cart(user_id, restaurant_id, cart_data, delivery_address, note, subtotal, shipping_fee, discount, delivery_time,
                           voucher_ids=None,initial_status=OrderState.PENDING):
    """
    Tạo một bản ghi Order và các OrderDetail tương ứng từ dữ liệu giỏ hàng trong session.
    """
    try:
        with db.session.begin_nested():
            total = subtotal + shipping_fee - discount
            new_order = Order(
                user_id=user_id,
                restaurant_id=restaurant_id,
                subtotal=subtotal,
                shipping_fee=shipping_fee,
                discount=discount,
                total=total,
                delivery_address=delivery_address,
                note=note,
                order_status=initial_status,
                delivery_time = delivery_time
            )

            if voucher_ids:
                vouchers = Voucher.query.filter(Voucher.id.in_(voucher_ids)).all()
                if vouchers:
                    new_order.vouchers.extend(vouchers)

            db.session.add(new_order)

            for item_key, item_info in cart_data['items'].items():
                detail = OrderDetail(
                    order=new_order,
                    dish_id=item_info['dish_id'],
                    quantity=item_info['quantity'],
                    price=item_info['price'],
                    dish_name=item_info['name'],
                    selected_options_luc_dat={
                        'options': item_info['options'],
                        'note': item_info.get('note', '')
                    }
                )
                db.session.add(detail)

        db.session.commit()
        return new_order
    except Exception as e:
        db.session.rollback()
        print(f"Lỗi khi tạo đơn hàng từ giỏ hàng: {e}")
        raise e

# 3.3.10 Module Momo, chatbot (Google AI)
def create_payment_record(order: Order, payment_method: str):
    """Tạo một bản ghi thanh toán mới cho một đơn hàng."""
    payment = Payment(
        order_id=order.id,
        amount=order.total,
        payment_method=payment_method,
        payment_status=PaymentStatus.UNPAID
    )
    db.session.add(payment)
    db.session.commit()
    return payment

import uuid
import hmac
import requests

def create_momo_payment_request(payment: Payment):
    """
    Tạo yêu cầu thanh toán đến MoMo và trả về URL thanh toán.
    Args:
        payment: Đối tượng Payment vừa được tạo.
    Returns:
        URL thanh toán của MoMo hoặc None nếu có lỗi.
    """
    PARTNER_CODE = app.config.get('MOMO_PARTNER_CODE')
    ACCESS_KEY = app.config.get('MOMO_ACCESS_KEY')
    SECRET_KEY = app.config.get('MOMO_SECRET_KEY')
    IPN_URL_BASE = app.config.get('MOMO_IPN_URL_BASE')
    REDIRECT_ID = payment.order_id
    REDIRECT_URL = app.config.get('MOMO_REDIRECT_URL')
    MOMO_ENDPOINT = app.config.get('MOMO_ENDPOINT')
    print(PARTNER_CODE)

    order_id_momo = str(uuid.uuid4()) # Tạo một ID duy nhất cho giao dịch MoMo
    request_id = str(uuid.uuid4())
    amount = str(int(payment.amount))
    order_info = f"Thanh toan don hang #{payment.order_id}"
    ipn_url = f"{IPN_URL_BASE}/{payment.id}" # MoMo sẽ gọi về URL này
    redirect_url = f"{REDIRECT_URL}/track-order/{REDIRECT_ID}"
    extra_data = ""

    raw_signature = (
        f"accessKey={ACCESS_KEY}&amount={amount}&extraData={extra_data}"
        f"&ipnUrl={ipn_url}&orderId={order_id_momo}&orderInfo={order_info}"
        f"&partnerCode={PARTNER_CODE}&redirectUrl={redirect_url}"
        f"&requestId={request_id}&requestType=captureWallet"
    )
    print(raw_signature)

    signature = hmac.new(SECRET_KEY.encode(), raw_signature.encode(), hashlib.sha256).hexdigest()

    payload = {
        'partnerCode': PARTNER_CODE,
        'requestId': request_id,
        'amount': amount,
        'orderId': order_id_momo,
        'orderInfo': order_info,
        'redirectUrl': redirect_url,
        'ipnUrl': ipn_url,
        'lang': "vi",
        'extraData': extra_data,
        'requestType': 'captureWallet',
        'signature': signature
    }

    try:
        response = requests.post(MOMO_ENDPOINT, data=json.dumps(payload), headers={'Content-Type': 'application/json'})
        response_data = response.json()

        if response_data.get("resultCode") == 0:
            payment.momo_order_id = order_id_momo
            payment.pay_url = response_data.get("payUrl")
            db.session.commit()
            return response_data.get("payUrl")
        else:
            print(f"Lỗi MoMo: {response_data.get('message')}")
            return None
    except Exception as e:
        print(f"Lỗi khi gọi MoMo API: {e}")
        return None
def get_active_orders_for_user(user_id):
    """
    Lấy danh sách các đơn hàng đang hoạt động
    của một người dùng.
    """
    # Các trạng thái được coi là "không hoạt động"
    inactive_statuses = [OrderState.COMPLETED]

    return Order.query.filter(
        Order.user_id == user_id,
        ~Order.order_status.in_(inactive_statuses) # Dấu ~ có nghĩa là NOT IN
    ).order_by(Order.order_date.desc()).all()

@event.listens_for(Order, 'after_update')
def emit_status_update_on_change(mapper, connection, target):
    """
    Tự động phát sự kiện SocketIO mỗi khi trạng thái đơn hàng được cập nhật.
    'target' chính là đối tượng Order vừa được cập nhật.
    """
    # Lấy lịch sử thay đổi của thuộc tính 'order_status'
    history = inspect(target).get_history('order_status', True)

    # Kiểm tra xem thuộc tính này có thực sự thay đổi không
    if history.has_changes():
        # Phát sự kiện đến client
        socketio.emit('order_status_updated', {
            'order_id': target.id,
            'status': target.order_status.value
        })
from datetime import date
from sqlalchemy import func
def count_orders_for_restaurant_today(restaurant_id):
    """Đếm số lượng đơn hàng của một nhà hàng trong ngày hôm nay."""
    today = date.today()
    # Câu lệnh này sẽ đếm tất cả các đơn hàng có restaurant_id khớp
    # và có ngày đặt hàng (chỉ lấy phần ngày, bỏ qua giờ) là ngày hôm nay.
    count = db.session.query(Order).filter(
        Order.restaurant_id == restaurant_id,
        func.date(Order.order_date) == today
    ).count()
    return count

import google.generativeai as genai

def call_gemini_api(user_message):
    """
    Gửi tin nhắn đến Google Gemini API và nhận phản hồi.
    """
    GOOGLE_API_KEY = app.config.get('GOOGLE_API_KEY')

    try:
        # Lấy API key từ biến môi trường đã được tải
        api_key = GOOGLE_API_KEY
        if not api_key:
            return "Lỗi: API Key của Google chưa được cấu hình."

        genai.configure(api_key=api_key)

        # Cấu hình model
        generation_config = {
            "temperature": 0.9,
            "top_p": 1,
            "top_k": 1,
            "max_output_tokens": 2048,
        }
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash-lite",
            generation_config=generation_config
        )

        # Bắt đầu cuộc trò chuyện và gửi tin nhắn
        convo = model.start_chat(history=[])
        convo.send_message(user_message)

        # Trả về phần văn bản của phản hồi
        return convo.last.text

    except Exception as e:
        print(f"Lỗi khi gọi Gemini API: {e}")
        return "Xin lỗi, trợ lý ảo đang gặp sự cố. Vui lòng thử lại sau."
#Khuyến mãi
def get_vouchers_by_restaurant(restaurant_id):
    return Voucher.query.filter_by(restaurant_id=restaurant_id).order_by(desc(Voucher.end_date)).all()

def get_voucher_by_id(voucher_id):
    return db.session.get(Voucher, voucher_id)

def add_voucher(data):
    try:
        new_voucher = Voucher(**data)
        db.session.add(new_voucher)
        db.session.commit()
        return new_voucher
    except Exception as e:
        print(f"Lỗi khi thêm voucher: {e}")
        db.session.rollback()
        return None

def update_voucher(voucher_id, data):
    voucher = get_voucher_by_id(voucher_id)
    if voucher:
        try:
            for key, value in data.items():
                setattr(voucher, key, value)
            db.session.commit()
            return voucher
        except Exception as e:
            print(f"Lỗi khi cập nhật voucher: {e}")
            db.session.rollback()
            return None
    return None

def delete_voucher(voucher_id):
    """Xóa một voucher khỏi cơ sở dữ liệu."""
    voucher = get_voucher_by_id(voucher_id)
    if voucher:
        try:
            db.session.delete(voucher)
            db.session.commit()
            return True
        except Exception as e:
            print(f"Lỗi khi xóa voucher: {e}")
            db.session.rollback()
            return False
    return False
#Order_Restaurant
def get_orders_by_restaurant(restaurant_id):
    try:
        query = Order.query \
            .filter_by(restaurant_id=restaurant_id) \
            .order_by(desc(Order.order_date)) \
            .all()

        return query
    except Exception as e:
        print(f"Lỗi khi lấy đơn hàng theo nhà hàng: {e}")
        return []
def get_order_by_id(order_id):
    return Order.query.get(order_id)

def get_raw_orders_in_range(self, restaurant_id, start_date, end_date):
        orders = db.session.query(Order).filter(
            Order.restaurant_id == restaurant_id,
            Order.order_date >= start_date,
            Order.order_date <= end_date
        ).all()
        return orders
if __name__ == "__main__":
    print(auth_user("user", 123))