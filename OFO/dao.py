import json
import os
import config
import hashlib
from  models import *
from __init__ import db,app
import cloudinary.uploader
from sqlalchemy import func, event, text
from sqlalchemy.orm import subqueryload, joinedload
from flask import request, jsonify
import traceback

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
def add_dishgroup(name, restaurant_id):
    """
    Thêm nhóm món, kiểm tra tên trùng lặp trong chính nhà hàng đó.
    Phiên bản ngắn gọn và an toàn.
    """
    # Kiểm tra xem tên nhóm món đã tồn tại trong cùng một nhà hàng chưa
    if DishGroup.query.filter(
        DishGroup.restaurant_id == restaurant_id,
        func.lower(DishGroup.name) == name.lower()
    ).first():
        return {'success': False, 'message': 'Tên nhóm món này đã tồn tại.'}

    try:
        # Nếu chưa tồn tại, tạo mới và lưu vào DB
        new_group = DishGroup(name=name.strip(), restaurant_id=restaurant_id)
        db.session.add(new_group)
        db.session.commit()

        # Trả về thông tin của nhóm vừa tạo để tiện xử lý ở frontend
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
    """
    Xóa nhóm món và tất cả các món ăn thuộc về nó.
    """
    group = DishGroup.query.get(group_id)

    if group:
        try:
            # BƯỚC 1: Lặp qua và xóa tất cả các món ăn con trước
            for dish in group.dishes:
                db.session.delete(dish)

            # BƯỚC 2: Sau khi đã xóa hết con, xóa chính người cha (nhóm món)
            db.session.delete(group)

            # BƯỚC 3: Commit một lần duy nhất để lưu tất cả thay đổi
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()  # Hủy bỏ nếu có lỗi
            print(f"LỖI KHI XÓA NHÓM MÓN VÀ CÁC MÓN ĂN: {e}")
            return False

    return False  # Trả về False nếu không tìm thấy nhóm món
def add_dish(name, description, price, image_url, dish_group_id, restaurant_id):
    try:
        dish = Dish(
            name=name,
            description=description,
            price=price,
            image=image_url,
            dish_group_id=dish_group_id,
            restaurant_id=restaurant_id
        )
        db.session.add(dish)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print("❌ Lỗi khi thêm món ăn trong DAO:", e)
        return False
def update_dish(data, image_file=None):
    try:
        dish_id = int(data.get('dish_id'))
        dish = Dish.query.get(dish_id)
        if not dish:
            return False, "Món ăn không tồn tại"

        dish.name = data.get('name')
        dish.description = data.get('description')
        dish.price = float(data.get('price'))
        dish.dish_group_id = int(data.get('dish_group_id'))
        dish.restaurant_id = int(data.get('restaurant_id'))

        if image_file:
            filename = image_file.filename
            save_path = os.path.join('static/image', filename)
            os.makedirs('static/image', exist_ok=True)
            image_file.save(save_path)
            dish.image = f'image/{filename}'

        db.session.commit()
        return True, None
    except Exception as e:
        db.session.rollback()
        return False, str(e)
@app.route('/update_dish', methods=['POST'])
def update_dish_route():
    success, message = update_dish(request.form, request.files.get('image'))
    return jsonify({'success': success, 'message': message if not success else 'Cập nhật thành công'})
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
    """Truy vấn và trả về danh sách tất cả các loại hình nhà hàng."""
    try:
        return Category.query.all()
    except Exception as e:
        print(f"Lỗi khi lấy danh sách category: {e}")
        return []


def register_restaurant_and_user(username, email, password, phone, res_name, address,
                                 description, open_time, close_time, category_id,
                                 avatar_url=None, cover_url=None):
    """
    Lưu User và Restaurant, đã được sửa lại để khớp hoàn toàn với định nghĩa Model.
    Sử dụng phương pháp liên kết đối tượng của SQLAlchemy.
    """
    # 1. Kiểm tra dữ liệu trùng lặp (nên giữ lại để có phản hồi lỗi tốt)
    if User.query.filter_by(email=email.strip()).first():
        return (False, 'Email này đã được sử dụng cho một tài khoản khác.')
    if User.query.filter_by(phone=phone.strip()).first():
        return (False, 'Số điện thoại này đã được đăng ký.')

    # 2. Tiến hành đăng ký
    try:
        # Băm mật khẩu bằng MD5 theo yêu cầu
        hashed_password = hashlib.md5(password.encode('utf-8')).hexdigest()

        # Tạo đối tượng User
        new_user = User(
            name=username.strip(),
            email=email.strip(),
            password=hashed_password,
            phone=phone.strip(),
            avatar=avatar_url,
            role=UserRole.RESTAURANT
        )

        # Chuyển đổi chuỗi thời gian sang đối tượng time của Python
        open_t = datetime.datetime.strptime(open_time, '%H:%M').time()
        close_t = datetime.datetime.strptime(close_time, '%H:%M').time()

        # === ĐOẠN CODE QUAN TRỌNG NHẤT ĐÃ ĐƯỢC SỬA LẠI ===

        # Bước 1: Tạo đối tượng Restaurant với các thuộc tính của chính nó
        new_restaurant = Restaurant(
            restaurant_name=res_name,
            address=address,
            description=description,
            email=email.strip(),  # Model Restaurant cũng có email riêng
            open_time=open_t,
            close_time=close_t,
            image=cover_url,
            category_id=int(category_id)
            # Không truyền owner_user_id hay user_id ở đây
        )

        # Bước 2: Liên kết hai đối tượng với nhau thông qua thuộc tính 'backref'
        # SQLAlchemy sẽ tự động hiểu và điền giá trị cho cột 'owner_user_id'
        new_restaurant.user = new_user

        # Thêm cả hai đối tượng vào session
        db.session.add(new_user)
        db.session.add(new_restaurant)

        # Commit để lưu tất cả thay đổi vào DB
        db.session.commit()

        # Trả về thành công
        return (True, new_user)

    except Exception as e:
        # Nếu có lỗi, rollback để đảm bảo toàn vẹn dữ liệu
        db.session.rollback()
        print("‼️ ERROR TRONG DAO:", e)
        traceback.print_exc()
        return (False, 'Đã có lỗi xảy ra trong quá trình xử lý dữ liệu.')
def toggle_favorite(user_id, restaurant_id):
    """
    Thêm hoặc xóa một nhà hàng khỏi danh sách yêu thích của người dùng.
    Trả về 'added' nếu đã thêm, 'removed' nếu đã xóa.
    """
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

if __name__ == "__main__":
    print(auth_user("user", 123))