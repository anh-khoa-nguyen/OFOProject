import os
from __init__ import app, db, login
import dao
from flask_login import login_user, logout_user, login_required, current_user
from models import *
from flask import request, jsonify
from flask import session
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import cloudinary.uploader

@app.route("/", methods=['GET','POST'])
def index():
    categories = dao.load_categories(8)
    random_restaurants = dao.load_random_restaurants(limit=10)
    return render_template('index.html', categories=categories, restaurants=random_restaurants)

@app.route('/search')
def search():
    categories = dao.load_categories(8)
    return render_template('tim-kiem.html', categories=categories)

@app.route('/restaurant/<int:restaurant_id>')
def restaurant_detail(restaurant_id):
    """
    Route này hiển thị trang chi tiết cho một nhà hàng cụ thể.
    """
    restaurant = dao.get_restaurant_by_id(restaurant_id)
    is_favorited = False
    if current_user.is_authenticated:
        is_favorited = dao.is_favorite(user_id=current_user.id, restaurant_id=restaurant_id)

    if not restaurant:
        return "Nhà hàng không tồn tại!", 404

    return render_template('restaurant_detail.html', restaurant=restaurant, is_favorited=is_favorited)

@app.route('/api/dish/<int:dish_id>')
def get_dish_options_api(dish_id):
    """
    API endpoint để lấy thông tin chi tiết của một món ăn và các tùy chọn của nó
    để hiển thị trong offcanvas.
    """
    try:
        dish = dao.get_dish_with_options(dish_id)

        if not dish:
            return jsonify({'error': 'Món ăn không tồn tại'}), 404

        # Chuyển đổi dữ liệu thành cấu trúc JSON
        response_data = {
            'id': dish.id,
            'name': dish.name,
            'description': dish.description,
            'price': dish.price,
            'image': dish.image,
            'option_groups': [
                {
                    'id': group.id,
                    'name': group.name,
                    'mandatory': group.mandatory,
                    'max_selection': group.max,
                    'options': [
                        {
                            'id': option.id,
                            'name': option.name,
                            'price_change': option.price
                        } for option in group.options
                    ]
                } for group in dish.option_groups
            ]
        }
        return jsonify(response_data)

    except Exception as e:
        print(f"Lỗi tại API get_dish_options_api: {e}")
        return jsonify({'error': 'Lỗi hệ thống'}), 500


@app.route('/search/<string:category_name>')
def search_by_category(category_name):
    restaurants_found = dao.search_restaurants(category_name=category_name)

    # Lấy tất cả các danh mục để hiển thị trong thanh cuộn
    all_categories = dao.load_categories()

    # Lấy đối tượng danh mục đã tìm kiếm để hiển thị tiêu đề

    # Render template tim-kiem.html và truyền dữ liệu vào
    return render_template('tim-kiem.html',
                           restaurants=restaurants_found,
                           categories=all_categories,
                         )

@app.route('/rating')
def rating():
    return render_template('rating.html')


@app.route('/rating/<int:order_id>', methods=['GET', 'POST'])
def rating_page(order_id):
    order = dao.Order.query.get(order_id)

    # --- Các bước kiểm tra an toàn (giữ nguyên) ---
    if not order:
        flash("Đơn hàng không tồn tại!", "danger")
        return redirect(url_for('index'))
    # if order.user_id != current_user.id:
    #     flash("Bạn không có quyền đánh giá đơn hàng này.", "danger")
    #     return redirect(url_for('index'))
    if order.review:
        flash("Đơn hàng này đã được bạn đánh giá rồi.", "info")
        return redirect(url_for('restaurant_detail', restaurant_id=order.restaurant_id))

    if request.method == 'POST':
        try:
            star = request.form.get('rating')
            comment = request.form.get('comment')

            # Lấy danh sách các file ảnh từ form
            images = request.files.getlist('images')

            if not star or not comment:
                return jsonify({'success': False, 'message': 'Vui lòng cho điểm và viết nhận xét.'}), 400

            # --- LOGIC UPLOAD ẢNH ---
            uploaded_urls = []
            if images:
                for image in images:
                    # Kiểm tra xem file có thực sự được gửi lên không
                    if image and image.filename != '':
                        # Upload lên Cloudinary
                        res = cloudinary.uploader.upload(image)
                        # Lấy URL an toàn và thêm vào danh sách
                        uploaded_urls.append(res.get('secure_url'))

            # Gọi hàm DAO để lưu đánh giá, truyền cả danh sách URL vào
            dao.add_review(
                order_id=order_id,
                star=int(star),
                comment=comment,
                image_urls=uploaded_urls  # Truyền danh sách URL
            )

            return jsonify({'success': True, 'message': 'Cảm ơn bạn đã gửi đánh giá!'})

        except ValueError as e:
            return jsonify({'success': False, 'message': str(e)}), 400
        except Exception as e:
            print(f"Lỗi khi lưu đánh giá: {e}")
            return jsonify({'success': False, 'message': 'Đã có lỗi xảy ra, vui lòng thử lại.'}), 500

    # --- HIỂN THỊ TRANG KHI LÀ GET REQUEST (giữ nguyên) ---
    restaurant = dao.get_restaurant_by_id(order.restaurant_id)
    return render_template('rating.html', restaurant=restaurant, order=order)


@app.route('/review/<int:restaurant_id>')
def restaurant_reviews(restaurant_id):
    # Lấy đối tượng nhà hàng, đã bao gồm 'star_average'
    restaurant = dao.get_restaurant_by_id(restaurant_id)

    if not restaurant:
        flash("Nhà hàng không tồn tại!", "danger")
        return redirect(url_for('index'))

    # Lấy danh sách chi tiết các review
    reviews = dao.get_reviews_by_restaurant(restaurant_id)

    # Lấy dữ liệu tổng hợp (tổng số review và phân phối sao)
    summary_data = dao.get_restaurant_review_summary(restaurant_id)

    # Render template và truyền tất cả dữ liệu vào
    return render_template('review.html',
                           restaurant=restaurant,
                           reviews=reviews,
                           summary_data=summary_data)

@app.route('/api/toggle-favorite/<int:restaurant_id>', methods=['POST'])
@login_required
def toggle_favorite_api(restaurant_id):
    """
    API endpoint để thêm hoặc xóa một nhà hàng khỏi danh sách yêu thích.
    """
    try:
        # Gọi hàm DAO để thực hiện logic
        status = dao.toggle_favorite(user_id=current_user.id, restaurant_id=restaurant_id)
        # Trả về kết quả thành công và trạng thái mới
        return jsonify({'success': True, 'status': status})
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 404
    except Exception as e:
        print(f"Lỗi tại toggle_favorite_api: {e}")
        return jsonify({'success': False, 'message': 'Đã có lỗi xảy ra.'}), 500


@app.route('/api/set-address', methods=['POST'])
def set_delivery_address():
    """
    API endpoint để nhận địa chỉ, kinh độ, vĩ độ và lưu vào session.
    """
    data = request.get_json()
    address = data.get('address')
    lat = data.get('lat')
    lng = data.get('lng')

    if not address or lat is None or lng is None:
        return jsonify({'success': False, 'message': 'Dữ liệu địa chỉ không đầy đủ.'}), 400

    # Lưu cả 3 thông tin vào session
    session['delivery_address'] = address
    session['delivery_latitude'] = lat
    session['delivery_longitude'] = lng

    return jsonify({'success': True, 'message': 'Đã cập nhật địa chỉ giao hàng.'})


@app.route('/clear-address')
def clear_delivery_address():
    """
    Xóa tất cả thông tin địa chỉ khỏi session và chuyển hướng về trang chủ.
    """
    session.pop('delivery_address', None)
    session.pop('delivery_latitude', None)
    session.pop('delivery_longitude', None)
    return redirect(url_for('index'))


@app.context_processor
def inject_delivery_address():
    """
    Làm cho các biến địa chỉ có sẵn trong tất cả các template.
    """
    return dict(
        delivery_address=session.get('delivery_address', '...'),
        delivery_latitude=session.get('delivery_latitude'),
        delivery_longitude=session.get('delivery_longitude')
    )

@app.route('/login',methods=['GET', 'POST'])
def login_view():
    error = None
    if request.method == 'POST':
        phone = request.form.get('phone')
        password = request.form.get('password')

        if not phone or not password:
            error = "Vui lòng nhập đầy đủ thông tin"
            return render_template('login.html', error=error)
        if len(phone) == 9 and not phone.startswith('0'):
            phone = '0' + phone

        # Xác thực người dùng và lấy thông tin vai trò
        u = dao.auth_user(phone=phone, password=password)
        if u:
            login_user(u)
            if u.role == UserRole.ADMIN:
                return redirect('/admin/')
            else:
                return redirect('/')
        else:
            error = "Tên đăng nhập hoặc mật khẩu không đúng."
            return render_template('login.html', error=error)
    return render_template('login.html')

@app.route("/logout")
def logout_process():
    logout_user()
    return redirect('/login')


@app.route('/preregister', methods=['GET', 'POST'])
def preregister():
    if request.method == 'POST':
        phone = request.form.get('phone')


        # Kiểm tra số điện thoại trống
        if not phone:
            flash("Vui lòng nhập số điện thoại", "danger")
            return render_template('preregister.html')

        phone = phone.strip()
        if len(phone) == 9 and not phone.startswith('0'):
            phone = '0' + phone

        # Xử lý định dạng số điện thoại
        if (phone.startswith('0') and len(phone) != 10) or (not phone.startswith('0') and len(phone) != 9) or not phone.isdigit():
            flash("Số điện thoại không hợp lệ! Vui lòng nhập đúng định dạng.", "danger")
            return render_template('preregister.html', phone=phone)

        # Kiểm tra số điện thoại đã tồn tại
        existing_user = User.query.filter_by(phone=phone).first()
        if existing_user:
            flash("Số điện thoại này đã được đăng ký!", "danger")
            return render_template('preregister.html', phone=phone)

        # Nếu chưa tồn tại thì chuyển sang đăng ký
        session['phone'] = phone
        return redirect(url_for('register', phone=phone))
    return render_template('preregister.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    phone = request.args.get('phone')  # Nhận phone từ URL
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        avatar = request.files.get('avatar')

        if password != confirm_password:
            flash('Mật khẩu xác nhận không khớp', 'danger')
            return render_template('register.html')
        else:
            data = request.form.copy()
            del data['confirm_password']

            # Xử lý phone: nếu chưa có số 0 ở đầu thì thêm vào
            phone = data.get('phone', '').replace(' ', '')
            if not phone.startswith('0'):
                phone = '0' + phone
            data['phone'] = phone  # cập nhật lại vào dict

        dao.add_user(avatar = avatar,**data)
        return redirect('/login')

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

@login.user_loader
def get_user_by_id(user_id):
    return dao.get_user_by_id(user_id)
import admin
if __name__ == '__main__':
    with app.app_context():
        import admin
        app.run(debug=True)
