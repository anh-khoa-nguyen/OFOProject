from flask import Flask, render_template, request, redirect, url_for, flash
from __init__ import app, db
import dao
import os

from dao import DishGroup
from flask import jsonify
IMAGE_FOLDER = 'static/image'
@app.route("/")
def index():
    return render_template('restaurant_detail.html')


@app.route('/login')
def login():
    return render_template('login.html')
  
@app.route('/preregister', methods=['GET', 'POST'])
def preregister():
    if request.method == 'POST':
        phone = request.form.get('phone')
        # Kiểm tra số điện thoại, xử lý logic tại đây nếu cần
        return redirect(url_for('register', phone=phone))
    return render_template('preregister.html')

@app.route('/register')
def register():
    phone = request.args.get('phone')  # Nhận phone từ URL
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Mật khẩu xác nhận không khớp', 'danger')
            return render_template('register.html')

    return render_template('register.html', phone=phone)
  
#Restaurant
@app.route('/resregister')
def resregister():
    return render_template('Restaurant/ResRegister.html')

@app.route('/reslogin')
def reslogin():
    return render_template('Restaurant/ResLogin.html')
@app.route('/restaurant')
def home():
    restaurant_id = 1  # Hoặc lấy theo session, hoặc query param
    dish_groups = dao.get_dish_groups_by_restaurant(restaurant_id)
    print("Dish groups:", dish_groups)
    return render_template('restaurant_main.html',restaurant=restaurant_id, dish_groups=dish_groups,)
@app.route('/add_dishgroup', methods=['POST'])
def add_dishgroup_route():
    data = request.get_json()
    name = data.get('name')
    restaurant_id = 1#data.get('restaurant_id')

    result = dao.add_dishgroup(name, restaurant_id)
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 400
@app.route('/delete_dishgroup/<int:group_id>', methods=['DELETE'])
def delete_dishgroup(group_id):
    try:
        from dao import delete_dishgroup_by_id
        success = delete_dishgroup_by_id(group_id)
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': 'Không tìm thấy nhóm món'}), 404
    except Exception as e:
        print('Lỗi:', e)
        return jsonify({'success': False, 'message': 'Lỗi server'}), 500

@app.route('/add_dish', methods=['POST'])
def add_dish_route():
    try:
        name = request.form.get('name')
        description = request.form.get('description')
        price = float(request.form.get('price'))
        dish_group_id = int(request.form.get('dish_group_id'))
        restaurant_id = int(request.form.get('restaurant_id'))
        image = request.files.get('image')

        image_url = None
        if image:
            upload_dir = 'static/image'
            os.makedirs(upload_dir, exist_ok=True)
            filename = image.filename
            path = os.path.join(upload_dir, filename)
            image.save(path)
            image_url = f"image/{filename}"

        success = dao.add_dish(name, description, price, image_url, dish_group_id, restaurant_id)
        return jsonify({'success': success})

    except Exception as e:
        print("❌ Lỗi khi thêm món ăn (route):", e)
        return jsonify({'success': False, 'message': str(e)})
@app.route('/delete_dish', methods=['POST'])
def delete_dish_route():
    try:
        data = request.get_json()
        dish_id = data.get('dish_id')
        success, message = dao.delete_dish(dish_id)
        return jsonify({'success': success, 'message': message})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
@app.route('/register_restaurant', methods=['POST'])
def register_restaurant():
    try:
        name = request.form.get('res-name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm-password')

        if password != confirm_password:
            return jsonify({'success': False, 'message': 'Mật khẩu không khớp'})

        # xử lý file ảnh
        avatar = request.files.get('avatar')
        cover = request.files.get('cover')

        avatar_path = None
        cover_path = None

        if avatar:
            avatar_path = os.path.join('static/image', avatar.filename)
            avatar.save(avatar_path)
        if cover:
            cover_path = os.path.join('static/image', cover.filename)
            cover.save(cover_path)

        dao.add_restaurant(
            name=name,
            email=email,
            address=request.form.get('address'),
            description=request.form.get('description'),
            open_time=request.form.get('open-time'),
            close_time=request.form.get('close-time'),
            avatar=avatar.filename if avatar else None,
            cover=cover.filename if cover else None
        )

        return jsonify({'success': True})
    except Exception as ex:
        return jsonify({'success': False, 'message': f'Đăng ký thất bại: {str(ex)}'})
@app.route("/tim-kiem")
def tim_kiem():
    return render_template('tim-kiem.html')

if __name__ == '__main__':
    with app.app_context():
        app.run(debug=True)
