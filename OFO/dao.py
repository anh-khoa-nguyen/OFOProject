import json
import os

from flask import request, jsonify
from werkzeug.security import generate_password_hash

import config
from sqlalchemy import text
from sqlalchemy import func
from __init__ import app, db
from models import DishGroup,Dish,Restaurant
def auth_user(username, password):
    current_dir = config.project_dir
    filepath = os.path.join(current_dir, 'data', 'users.json')  # tức là OFO/data/users.json

    with open(filepath, encoding="utf-8") as f:
        users = json.load(f)

        for u in users:
            if u["username"] == username and u["password"] == password:
                return True

    return False
#Load restaurant_main:
def get_dish_groups_by_restaurant(restaurant_id):
    return DishGroup.query.filter_by(restaurant_id=restaurant_id).all()
def add_dishgroup(name, restaurant_id):
    # Kiểm tra xem tên nhóm đã tồn tại (không phân biệt chữ hoa thường)
    existing = db.session.query(DishGroup).filter(
        func.lower(DishGroup.name) == name.lower()
    ).first()

    if existing:
        return {'success': False, 'message': 'Tên nhóm món đã tồn tại'}

    new_group = DishGroup(name=name, restaurant_id=restaurant_id)
    db.session.add(new_group)
    db.session.commit()
    return {'success': True, 'message': 'Thêm nhóm món thành công'}
def delete_dishgroup_by_id(group_id):
    group = DishGroup.query.get(group_id)
    if group:
        db.session.delete(group)
        db.session.commit()
        return True
    return False
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
def add_restaurant(name, email, address, description, open_time, close_time, avatar, cover):
    restaurant = Restaurant(
        restaurant_name=name,
        email=email,
        address=address,
        description=description,
        open_time=open_time,
        close_time=close_time,
        image=avatar,  # dùng avatar làm ảnh đại diện
        owner_user_id=1  # hoặc session['user_id'] nếu có đăng nhập
    )
    db.session.add(restaurant)
    db.session.commit()
def authenticate_restaurant(email, password):
    restaurant = Restaurant.query.filter_by(email=email).first()
    if restaurant and check_password_hash(restaurant.password, password):
        return restaurant
    return None
if __name__ == "__main__":
    print(auth_user("user", 123))