import os, json
from __init__ import app, db, login
import dao
from flask_login import login_user, logout_user, login_required, current_user
from models import *
from flask import session
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import cloudinary.uploader
from datetime import datetime, timezone
from geopy.distance import geodesic
from flask_socketio import join_room
from __init__ import socketio

@app.route("/", methods=['GET','POST'])
def index():
    categories = dao.load_categories(8)

    delivery_address = session.get('delivery_address')
    user_lat = session.get('delivery_latitude')
    user_lng = session.get('delivery_longitude')

    if delivery_address:
        restaurants_to_show = dao.load_random_restaurants(
            limit=10,
            user_lat=user_lat,
            user_lng=user_lng
        )
    else:
        restaurants_to_show = dao.get_top_rated_restaurants(limit=10)

    return render_template('index.html', categories=categories, restaurants=restaurants_to_show)

@app.route('/search')
def search():
    """
    Route tìm kiếm chính, xử lý cả tìm kiếm theo vị trí và danh mục.
    """
    # Lấy các tham số từ URL và session
    category_name = request.args.get('category_name')
    user_lat = session.get('delivery_latitude')
    user_lng = session.get('delivery_longitude')

    print( user_lat)
    print(user_lng)

    # Gọi hàm DAO mới, nó sẽ trả về một tuple gồm 2 danh sách
    nearby_restaurants, other_restaurants = dao.search_and_classify_restaurants(
        category_name=category_name,
        user_lat=user_lat,
        user_lng=user_lng,
        radius_km=10
    )

    other_restaurants_data = [
        {
            "id": r.id,
            "name": r.restaurant_name,
            "image": r.image,
            "category": r.category.name if r.category else 'Nhà hàng',
            "stars": r.star_average or 'Mới',
            "time": r.delivery_time_minutes,
            "distance": r.distance_km,
            # Rất quan trọng: phải có dữ liệu này để bộ lọc realtime hoạt động
            "dish_names": '|'.join([d.name for d in r.dishes]).lower()
        } for r in other_restaurants
    ]

    all_categories = dao.load_categories()
    searched_category = dao.get_category_by_name(category_name) if category_name else None

    return render_template('tim-kiem.html',
                           nearby_restaurants=nearby_restaurants,
                           other_restaurants=other_restaurants,
                           # Truyền dữ liệu JSON cho JavaScript
                           other_restaurants_json=json.dumps(other_restaurants_data),
                           categories=all_categories,
                           searched_category=searched_category)

@app.route('/search/<string:category_name>')
def search_by_category(category_name):
    """
    Route cũ này giờ sẽ chuyển hướng đến route tìm kiếm chính.
    Điều này đảm bảo các link cũ không bị hỏng.
    """
    return redirect(url_for('search', category_name=category_name))

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
    if order.user_id != current_user.id:
        flash("Bạn không có quyền đánh giá đơn hàng này.", "danger")
        return redirect(url_for('index'))
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
        greeting=dao.get_greeting(),
        random_slogan=dao.get_random_slogan(),
        delivery_address=session.get('delivery_address', '...'),
        delivery_latitude=session.get('delivery_latitude'),
        delivery_longitude=session.get('delivery_longitude'),
        chat_history = session.get('chat_history', [])
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
            elif u.role == UserRole.RESTAURANT:
                restaurant = dao.get_restaurant_by_user_id(u.id)
                session['restaurant_id'] = restaurant.id
                return redirect(f"/restaurante/{restaurant.id}")
            else:
                return redirect('/')

        else:
            error = "Tên đăng nhập hoặc mật khẩu không đúng."
            return render_template('login.html', error=error)
    return render_template('login.html')

@app.route("/logout")
def logout_process():
    logout_user()
    session.pop('restaurant_id', None)
    session.pop('cart', None)
    session.pop('chat_history', None)
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

def render_registration_page():
    """Hiển thị trang đăng ký và truyền danh sách category."""
    categories = dao.get_categories()
    return render_template('Restaurant/ResRegister.html', categories=categories)

@app.route('/reslogin')
def reslogin():
    return render_template('Restaurant/ResLogin.html')

@app.route('/restaurante/<int:restaurant_id>')
def home(restaurant_id):
    restaurant= dao.get_restaurant_by_id(restaurant_id)
    dish_groups = dao.get_dish_groups_by_restaurant(restaurant_id)
    dish_option_group= dao.get_dish_option_groups_by_restaurant(restaurant_id)
    return render_template('restaurant_main.html',restaurant=restaurant, dish_groups=dish_groups,dish_option_group=dish_option_group)

@app.route('/add_dishgroup', methods=['POST'])
def add_dishgroup_route():
    data = request.get_json()
    name = data.get('name')
    restaurant_id = session.get('restaurant_id')

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
        option_group_ids = request.form.getlist('option_group_ids')
        image = request.files.get('image')
        image_url = None
        if image:
            upload_result = cloudinary.uploader.upload(image)
            image_url = upload_result.get('secure_url')
        success = dao.add_dish(name, description, price, image_url, dish_group_id, restaurant_id,option_group_ids=option_group_ids)
        return jsonify({'success': success})

    except Exception as e:
        print("❌ Lỗi khi thêm món ăn (route):", e)
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/dish-details/<int:dish_id>', methods=['GET'])
def get_dish_details_api(dish_id):
    dish_data = dao.get_dish_details_for_edit(dish_id)
    if dish_data:
        return jsonify(dish_data)
    else:
        return jsonify({"error": "Không tìm thấy món ăn"}), 404



@app.route('/update_dish', methods=['POST'])
def update_dish_route():
    image = request.files.get('image')
    image_url = None
    if image:
        upload_result = cloudinary.uploader.upload(image)
        image_url = upload_result.get('secure_url')
    try:
        success, message = dao.update_dish_with_options(
            form_data=request.form,
            image_file=image_url
        )

        # Trả về kết quả cho frontend
        return jsonify({'success': success, 'message': message})

    except Exception as e:
        print(f"❌ Lỗi nghiêm trọng tại route /update_dish: {e}")
        return jsonify({'success': False, 'message': 'Lỗi hệ thống.'}), 500
@app.route('/delete_dish', methods=['POST'])
def delete_dish_route():
    try:
        data = request.get_json()
        dish_id = data.get('dish_id')
        success, message = dao.delete_dish(dish_id)
        return jsonify({'success': success, 'message': message})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
@app.route('/api/add_option_group', methods=['POST'])
def api_add_option_group():
    data = request.get_json()
    print("Dữ liệu nhận được từ form:", data)  # convert thành dict

    if not data:
        return jsonify({'success': False, 'message': 'Dữ liệu không hợp lệ.'}), 400
    new_group = dao.add_option_group_with_options(data)

    if new_group:
        return jsonify({
            'success': True,
            'message': 'Thêm nhóm tùy chọn thành công!',
            'group': { 'id': new_group.id, 'name': new_group.name }
        }), 201 # HTTP status 201 Created
    else:
        # Nếu thất bại, trả về lỗi server
        return jsonify({'success': False, 'message': 'Có lỗi xảy ra phía máy chủ.'}), 500
@app.route('/api/option-group/update', methods=['POST'])
def update_option_group_api():
    """
    API Endpoint để cập nhật nhóm tùy chọn.
    Chỉ nhận dữ liệu và gọi hàm xử lý từ DAO.
    """
    # 1. Nhận dữ liệu JSON từ frontend
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Không có dữ liệu được gửi.'}), 400

    # 2. Gọi hàm DAO để thực hiện logic cập nhật
    success, result = dao.update_option_group_with_options(data)

    # 3. Xử lý kết quả trả về từ DAO
    if success:
        # Nếu thành công, `result` là đối tượng group đã được cập nhật
        updated_group = result
        return jsonify({
            'success': True,
            'message': f'Đã cập nhật thành công nhóm "{updated_group.name}".'
        })
    else:
        # Nếu thất bại, `result` là chuỗi thông báo lỗi
        error_message = result
        # Trả về mã lỗi 400 (Bad Request) hoặc 404 (Not Found) tùy theo lỗi
        status_code = 404 if "Không tìm thấy" in error_message else 400
        return jsonify({
            'success': False,
            'message': error_message
        }), status_code
@app.route('/api/option-group/<int:group_id>', methods=['GET'])
def get_option_group_details_api(group_id):
    """
    API để cung cấp dữ_liệu chi tiết của một DishOptionGroup và các DishOption con.
    """
    # get_or_404 là cách tốt nhất, nó tự động trả về lỗi 404 nếu không tìm thấy ID
    group = DishOptionGroup.query.get_or_404(group_id)

    # Chuyển đổi đối tượng SQLAlchemy thành một dictionary để có thể gửi qua JSON
    group_data = {
        'id': group.id,
        'name': group.name,
        'max': group.max,
        'mandatory': group.mandatory,
        'options': [
            {'name': opt.name, 'price': opt.price} for opt in group.options
        ]
    }
    return jsonify(group_data)
@app.route('/api/option-group/delete/<int:group_id>', methods=['DELETE'])
def delete_option_group_api(group_id):
    success, message = dao.delete_option_group_by_id(group_id)
    if success:

        return jsonify({
            'success': True,
            'message': message
        })
    else:
        status_code = 404 if "Không tìm thấy" in message else 500
        return jsonify({
            'success': False,
            'message': message
        }), status_code
#ĐĂNG KÍ NHÀ HÀNG
@app.route('/register_restaurant', methods=['POST'])
def handle_restaurant_registration():
    """
    API endpoint xử lý đăng ký nhà hàng.
    Đã được sửa lại để lấy và lưu đầy đủ thông tin.
    """
    try:
        # 1. Lấy dữ liệu từ form-data (ĐÃ BỔ SUNG)
        form_data = request.form
        username = form_data.get('username')
        email = form_data.get('email')
        phone = form_data.get('phone')  # <- THÊM MỚI
        password = form_data.get('password')
        confirm_password = form_data.get('confirm-password')

        res_name = form_data.get('res-name')
        address = form_data.get('address')
        description = form_data.get('description')
        open_time = form_data.get('open-time')
        close_time = form_data.get('close-time')
        category_id = form_data.get('category_id')  # <- THÊM MỚI

        # 2. Lấy file từ request.files
        avatar_file = request.files.get('avatar')
        cover_file = request.files.get('cover')

        # 3. Xác thực dữ liệu ở phía server (ĐÃ CẬP NHẬT)
        required_fields = {
            "Tên người dùng": username, "Email": email, "Số điện thoại": phone,
            "Mật khẩu": password, "Tên nhà hàng": res_name, "Địa chỉ": address,
            "Giờ mở cửa": open_time, "Giờ đóng cửa": close_time, "Loại hình": category_id
        }
        for field_name, value in required_fields.items():
            if not value:
                return jsonify({'success': False, 'message': f'Vui lòng cung cấp thông tin "{field_name}".'}), 400

        if password != confirm_password:
            return jsonify({'success': False, 'message': 'Mật khẩu xác nhận không khớp.'}), 400

        # 4. Xử lý upload file lên Cloudinary (giữ nguyên)
        avatar_url = None
        if avatar_file:
            upload_result = cloudinary.uploader.upload(avatar_file)
            avatar_url = upload_result.get('secure_url')
        cover_url = None
        if cover_file:
            upload_result = cloudinary.uploader.upload(cover_file)
            cover_url = upload_result.get('secure_url')

        # 5. Gọi hàm DAO để lưu vào database (ĐÃ CẬP NHẬT ĐẦY ĐỦ)
        # Sử dụng lại cấu trúc trả về (success, result) để xử lý lỗi tốt hơn
        success, result = dao.register_restaurant_and_user(
            username=username,
            email=email,
            password=password,
            phone=phone,  # <- TRUYỀN VÀO
            res_name=res_name,
            address=address,
            description=description,
            open_time=open_time,
            close_time=close_time,
            category_id=category_id,  # <- TRUYỀN VÀO
            avatar_url=avatar_url,
            cover_url=cover_url
        )

        # 6. Trả kết quả về cho client
        if success:
            new_user = result
            return jsonify({
                'success': True,
                'message': f'Tài khoản {new_user.name} và nhà hàng {res_name} đã được tạo thành công!'
            }), 201
        else:
            # result ở đây là thông báo lỗi cụ thể (ví dụ: "Email đã tồn tại")
            error_message = result
            return jsonify({
                'success': False,
                'message': error_message
            }), 409  # 409 Conflict

    except Exception as e:
        print(f"Lỗi nghiêm trọng khi đăng ký: {e}")
        return jsonify({'success': False, 'message': 'Có lỗi xảy ra ở phía máy chủ.'}), 500
@app.route("/tim-kiem")
def tim_kiem():
    return render_template('tim-kiem.html')

# 3.3.6 Module Lịch sử và chi tiết đơn hàng, nhà hàng yêu thích
@app.route('/history')
@login_required
def order_history():
    # Lấy tất cả đơn hàng của người dùng hiện tại, sắp xếp từ mới nhất đến cũ nhất
    orders = dao.get_orders_by_user_id(current_user.id)
    return render_template('User/order_list.html', orders=orders)

@app.route('/order/<int:order_id>')
@login_required
def order_detail_page(order_id):
    # 1. Lấy thông tin chi tiết đơn hàng từ DAO
    order = dao.get_order_details_by_id(order_id)

    # 2. Kiểm tra xem đơn hàng có tồn tại không
    if not order:
        # Nếu không tìm thấy, trả về lỗi 404 Not Found
        return jsonify({'success': False, 'message': 'Không tìm thấy nhóm món'}), 404

    # 3. KIỂM TRA QUYỀN TRUY CẬP
    # Khai báo các điều kiện để dễ đọc
    is_the_customer = (current_user.id == order.user_id)
    is_an_admin = (current_user.role == UserRole.ADMIN)
    # Hàm DAO đã tải sẵn thông tin nhà hàng, nên truy cập order.restaurant không tốn thêm query
    is_the_restaurant_owner = (current_user.id == order.restaurant.owner_user_id)

    # Nếu người dùng không thỏa mãn BẤT KỲ điều kiện nào ở trên
    if not (is_the_customer or is_an_admin or is_the_restaurant_owner):
        # Trả về lỗi 403 Forbidden (Cấm truy cập)
        return jsonify({'success': False, 'message': 'Không tìm thấy nhóm món'}), 404

    # 4. Nếu tất cả kiểm tra đều qua, hiển thị trang
    return render_template('User/order_details.html', order=order)

@login.user_loader
def get_user_by_id(user_id):
    return dao.get_user_by_id(user_id)

# Trong file index.py

@app.route('/api/dish/<int:dish_id>')
def get_dish_details(dish_id):
    """
    API endpoint để trả về chi tiết của một món ăn dưới dạng JSON.
    """
    dish_details = dao.get_dish_details_by_id(dish_id)
    if dish_details:
        return jsonify(dish_details)
    return jsonify({"error": "Dish not found"}), 404



from dao import get_dish_by_id, get_options_by_ids

@app.route('/api/add-to-cart', methods=['POST'])
def add_to_cart():
    data = request.json
    dish_id = data.get('dish_id')
    quantity = int(data.get('quantity', 1))
    selected_option_ids = data.get('options', [])
    item_key_to_edit = data.get('item_key_to_edit')
    note = data.get('note', '')

    dish = get_dish_by_id(dish_id)
    if not dish:
        return jsonify({'success': False, 'message': 'Món ăn không tồn tại'}), 404

    cart = session.get('cart', {})
    restaurant_id_str = str(dish.restaurant_id)


    # Nếu đây là một lần chỉnh sửa, xóa món ăn cũ trước
    if item_key_to_edit and restaurant_id_str in cart and item_key_to_edit in cart[restaurant_id_str]['items']:
        del cart[restaurant_id_str]['items'][item_key_to_edit]

    if restaurant_id_str not in cart:
        cart[restaurant_id_str] = {
            'restaurant_name': dish.restaurant.restaurant_name,
            'restaurant_image': dish.restaurant.image,
            'items': {}
        }

    selected_option_ids.sort()
    unique_key = f"dish_{dish_id}_" + '_'.join(map(str, selected_option_ids))

    options_details = []
    options_price = 0
    if selected_option_ids:
        options = get_options_by_ids(selected_option_ids)
        for opt in options:
            options_details.append({'id': opt.id, 'name': opt.name, 'price': opt.price})
            options_price += opt.price

    final_price_per_item = dish.price + options_price

    if unique_key in cart[restaurant_id_str]['items']:
        cart[restaurant_id_str]['items'][unique_key]['quantity'] += quantity
        cart[restaurant_id_str]['items'][unique_key]['note'] = note
    else:
        cart[restaurant_id_str]['items'][unique_key] = {
            'dish_id': dish.id,
            'name': dish.name,
            'image': dish.image,
            'price': final_price_per_item,
            'quantity': quantity,
            'options': options_details,
            'note': note
        }

    session['cart'] = cart
    session.modified = True

    return jsonify({'success': True, 'message': 'Đã cập nhật giỏ hàng', 'cart': cart})

# Nên dùng Api thay vì ssesion vì gửi những thông tin nhạy cảm như là giá tiền, ng dùng có thể dùng F12 thay đổi giá tiền -> rất nguy hiểm
@app.route('/api/update-cart-item', methods=['POST'])
def update_cart_item():
    """
    API để cập nhật số lượng của một món ăn trong giỏ hàng.
    Nếu số lượng <= 0, món ăn sẽ bị xóa.
    """
    data = request.json
    restaurant_id = str(data.get('restaurant_id'))
    item_key = data.get('item_key')
    new_quantity = int(data.get('quantity', 1))

    cart = session.get('cart', {})

    if restaurant_id in cart and item_key in cart[restaurant_id]['items']:
        if new_quantity > 0:
            cart[restaurant_id]['items'][item_key]['quantity'] = new_quantity
        else:
            del cart[restaurant_id]['items'][item_key]
            if not cart[restaurant_id]['items']:
                del cart[restaurant_id]

        session['cart'] = cart
        session.modified = True
        return jsonify({'success': True, 'cart': cart})

    return jsonify({'success': False, 'message': 'Món ăn không tìm thấy trong giỏ'}), 404


@app.route('/api/delete-cart-item', methods=['POST'])
def delete_cart_item():
    """
    API để xóa hoàn toàn một món ăn khỏi giỏ hàng.
    """
    data = request.json
    restaurant_id = str(data.get('restaurant_id'))
    item_key = data.get('item_key')

    cart = session.get('cart', {})

    if restaurant_id in cart and item_key in cart[restaurant_id]['items']:
        del cart[restaurant_id]['items'][item_key]
        if not cart[restaurant_id]['items']:
            del cart[restaurant_id]

        session['cart'] = cart
        session.modified = True
        return jsonify({'success': True, 'cart': cart})

    return jsonify({'success': False, 'message': 'Món ăn không tìm thấy trong giỏ'}), 404

# Thêm vào file index.py

@app.route('/my-favorites')
@login_required # Đảm bảo chỉ người dùng đã đăng nhập mới truy cập được
def favorite_restaurants_page():

    favorite_list = current_user.favorite_restaurants.all()
    return render_template('favorite_restaurant.html', favorite_restaurants=favorite_list)

@app.context_processor
def inject_cart():
    return {
        'cart': session.get('cart', {})
    }


def _parse_voucher_form(form_data):
    """
    Hàm này phân tích và chuyển đổi dữ liệu từ form thành một dictionary
    sạch, sẵn sàng để lưu vào CSDL.
    """
    data = {}
    data['name'] = form_data.get('name')
    data['code'] = form_data.get('code', '').upper()
    data['description'] = form_data.get('description')
    data['percent'] = float(form_data.get('percent')) if form_data.get('percent') else None
    data['limit'] = float(form_data.get('limit')) if form_data.get('limit') else None
    data['min'] = float(form_data.get('min')) if form_data.get('min') else 0
    data['max'] = float(form_data.get('max')) if form_data.get('max') else None
    data['restaurant_id'] = form_data.get('restaurant_id')
    data['active'] = True if form_data.get('active') == 'on' else False

    start_date_str = form_data.get('start_date')
    end_date_str = form_data.get('end_date')

    if start_date_str:
        data['start_date'] = datetime.strptime(start_date_str, '%d/%m/%Y')
    if end_date_str:
        data['end_date'] = datetime.strptime(end_date_str, '%d/%m/%Y')

    return data

@app.route('/voucher/<int:restaurant_id>')
def voucher(restaurant_id):
    restaurant = dao.get_restaurant_by_id(restaurant_id)
    vouchers = dao.get_vouchers_by_restaurant(restaurant_id)

    return render_template(
        'Restaurant/Voucher.html',
        restaurant=restaurant,
        vouchers=vouchers
    )
@app.route('/api/vouchers/<int:voucher_id>', methods=['GET'])
def get_voucher_api(voucher_id):
    voucher = dao.get_voucher_by_id(voucher_id)
    if voucher:
        return jsonify({
            'id': voucher.id, 'name': voucher.name, 'code': voucher.code,
            'description': voucher.description, 'percent': voucher.percent,
            'limit': voucher.limit, 'min': voucher.min, 'max': voucher.max,
            'start_date': voucher.start_date.strftime('%d-%m-%Y'),
            'end_date': voucher.end_date.strftime('%d-%m-%Y'),
            'active': voucher.active
        })
    return jsonify({'error': 'Voucher not found'}), 404


# --- API ĐỂ TẠO MỚI MỘT VOUCHER ---
@app.route('/api/vouchers', methods=['POST'])
def create_voucher_api():
    print("Dữ liệu form nhận được:", request.form)
    try:
        data = _parse_voucher_form(request.form)
        new_voucher = dao.add_voucher(data)
        if new_voucher:
            return jsonify({'message': 'Tạo voucher thành công!', 'id': new_voucher.id}), 201
        return jsonify({'error': 'Không thể tạo voucher'}), 500
    except Exception as e:
        return jsonify({'error': f'Dữ liệu không hợp lệ: {e}'}), 400

@app.route('/api/vouchers/<int:voucher_id>', methods=['POST', 'PUT'])
def update_voucher_api(voucher_id):
    voucher = dao.get_voucher_by_id(voucher_id)
    if not voucher:
        return jsonify({'error': 'Voucher không tồn tại'}), 404
    try:
        data = _parse_voucher_form(request.form)
        data.pop('id', None)  # Bỏ id ra khỏi dữ liệu cập nhật
        updated_voucher = dao.update_voucher(voucher_id, data)
        if updated_voucher:
            return jsonify({'message': 'Cập nhật voucher thành công!'})
        return jsonify({'error': 'Cập nhật thất bại'}), 500
    except Exception as e:
        return jsonify({'error': f'Dữ liệu không hợp lệ: {e}'}), 400

@app.route('/api/vouchers/<int:voucher_id>', methods=['DELETE'])
def delete_voucher_api(voucher_id):
    success = dao.delete_voucher(voucher_id)
    if success:
        return jsonify({'message': 'Xóa voucher thành công!'})
    return jsonify({'error': 'Không tìm thấy voucher hoặc lỗi khi xóa'}), 404

@app.template_filter('format_currency')
def format_currency_filter(value):
    """
    Một bộ lọc Jinja2 an toàn để định dạng số thành tiền tệ.
    Nếu giá trị là None hoặc không phải là số, trả về một chuỗi rỗng.
    """
    if value is None:
        return "0đ"
    try:
        return f"{int(value):,}đ"
    except (ValueError, TypeError):
        return "0đ"


# Trong file index.py

# Trong file index.py

# @app.route('/checkout/<int:restaurant_id>', methods=['GET', 'POST'])
# @login_required
# def checkout(restaurant_id):
#     cart = session.get('cart', {})
#     restaurant_id_str = str(restaurant_id)
#
#     if restaurant_id_str not in cart:
#         flash('Giỏ hàng của bạn cho nhà hàng này đang trống.', 'warning')
#         return redirect(url_for('restaurant_detail', restaurant_id=restaurant_id))
#
#     restaurant_cart = cart[restaurant_id_str]
#     restaurant = dao.get_restaurant_by_id(restaurant_id)
#     subtotal = sum(item['price'] * item['quantity'] for item in restaurant_cart['items'].values())
#
#     user_lat = session.get('delivery_latitude')
#     user_lng = session.get('delivery_longitude')
#     distance_km = None
#     delivery_time = None
#     shipping_fee = 15000
#
#     if user_lat and user_lng and restaurant.lat and restaurant.lng:
#         distance_km = round(geodesic((user_lat, user_lng), (restaurant.lat, restaurant.lng)).km, 1)
#         delivery_time = round(10 + (distance_km * 5))
#         if distance_km <= 3:
#             shipping_fee = 15000
#         else:
#             shipping_fee = 15000 + (distance_km - 3) * 4000
#         shipping_fee = round(shipping_fee / 1000) * 1000
#
#     # --- XỬ LÝ POST REQUEST ---
#     if request.method == 'POST':
#         delivery_address = request.form.get('delivery_address')
#         note = request.form.get('note')
#         # SỬA LỖI 2: Nhận đúng tên 'voucher_ids'
#         voucher_ids_str = request.form.get('voucher_ids')
#         discount_amount = float(request.form.get('discount_amount', 0))
#         payment_method = request.form.get('payment_method')
#
#         voucher_ids = []
#         if voucher_ids_str:
#             voucher_ids = [int(vid) for vid in voucher_ids_str.split(',')]
#
#         if not delivery_address:
#             flash('Vui lòng nhập địa chỉ giao hàng.', 'danger')
#             # Nếu lỗi, phải render lại trang với đầy đủ context
#             all_valid_vouchers = dao.get_valid_vouchers(restaurant_id, subtotal)
#             shipping_vouchers_data = [v for v in all_valid_vouchers if 'FREESHIP' in v.code.upper()]
#             shop_vouchers_data = [v for v in all_valid_vouchers if 'FREESHIP' not in v.code.upper()]
#             return render_template('User/Order_Pay.html',
#                                    restaurant=restaurant,
#                                    cart_items=restaurant_cart['items'],
#                                    subtotal=subtotal,
#                                    shipping_fee=shipping_fee,
#                                    delivery_time=delivery_time,
#                                    distance_km=distance_km,
#                                    shipping_vouchers=shipping_vouchers_data,
#                                    shop_vouchers=shop_vouchers_data)
#
#         try:
#             order = dao.create_order_from_cart(
#                 user_id=current_user.id,
#                 restaurant_id=restaurant_id,
#                 cart_data=restaurant_cart,
#                 delivery_address=delivery_address,
#                 note=note,
#                 subtotal=subtotal,
#                 shipping_fee=shipping_fee,
#                 discount=discount_amount,
#                 voucher_ids=voucher_ids  # <-- Truyền danh sách ID
#             )
#
#             del session['cart'][restaurant_id_str]
#             session.modified = True
#
#             if payment_method == 'vnpay':
#                 flash('Chức năng thanh toán VNPay đang được phát triển.', 'info')
#                 return redirect(url_for('index'))
#             else:  # Thanh toán COD
#                 flash(f'Đặt hàng thành công! Đơn hàng #{order.id} đang được chuẩn bị.', 'success')
#                 return redirect(url_for('index'))
#
#         except Exception as e:
#             flash(f'Đã có lỗi xảy ra khi đặt hàng: {e}', 'danger')
#             # SỬA LỖI 1: Thêm 'return' ở đây
#             return redirect(url_for('checkout', restaurant_id=restaurant_id))
#
#     # --- XỬ LÝ GET REQUEST ---
#     all_valid_vouchers = dao.get_valid_vouchers(restaurant_id, subtotal)
#     shipping_vouchers_data = []
#     shop_vouchers_data = []
#     for v in all_valid_vouchers:
#         voucher_dict = {"id": v.id, "code": v.code, "name": v.name, "description": v.description, "percent": v.percent,
#                         "limit": v.limit, "max": v.max, "min": v.min}
#         if 'FREESHIP' in v.code.upper():
#             shipping_vouchers_data.append(voucher_dict)
#         else:
#             shop_vouchers_data.append(voucher_dict)
#
#     return render_template('User/Order_Pay.html',
#                            restaurant=restaurant,
#                            cart_items=restaurant_cart['items'],
#                            subtotal=subtotal,
#                            delivery_time=delivery_time,
#                            distance_km=distance_km,
#                            shipping_fee=shipping_fee,
#                            shipping_vouchers=shipping_vouchers_data,
#                            shop_vouchers=shop_vouchers_data)

@app.route('/checkout/<int:restaurant_id>', methods=['GET', 'POST'])
@login_required
def checkout(restaurant_id):
    cart = session.get('cart', {})
    restaurant_id_str = str(restaurant_id)

    # --- KIỂM TRA GIỎ HÀNG ---
    if restaurant_id_str not in cart or not cart[restaurant_id_str]['items']:
        flash('Giỏ hàng của bạn cho nhà hàng này đang trống.', 'warning')
        return redirect(url_for('restaurant_detail', restaurant_id=restaurant_id))

    restaurant_cart = cart[restaurant_id_str]
    restaurant = dao.get_restaurant_by_id(restaurant_id)
    subtotal = sum(item['price'] * item['quantity'] for item in restaurant_cart['items'].values())

    # --- TÍNH TOÁN PHÍ SHIP  ---
    user_lat = session.get('delivery_latitude')
    user_lng = session.get('delivery_longitude')
    distance_km, delivery_time, shipping_fee = None, None, 15000
    if user_lat and user_lng and restaurant.lat and restaurant.lng:
        distance_km = round(geodesic((user_lat, user_lng), (restaurant.lat, restaurant.lng)).km, 1)
        delivery_time = round(10 + (distance_km * 5))
        shipping_fee = round((15000 + max(0, distance_km - 3) * 4000) / 1000) * 1000

    # --- XỬ LÝ POST REQUEST  ---
    if request.method == 'POST':
        # 1. Lấy dữ liệu từ form
        delivery_address = request.form.get('delivery_address')
        note = request.form.get('note')
        voucher_ids_str = request.form.get('voucher_ids')
        discount_amount = float(request.form.get('discount_amount', 0))
        payment_method = request.form.get('payment_method')

        if not delivery_address:
            flash('Vui lòng chọn địa chỉ giao hàng.', 'danger')
            return redirect(url_for('checkout', restaurant_id=restaurant_id))

        # 2. Tạo đơn hàng trong CSDL
        try:
            voucher_ids = [int(vid) for vid in voucher_ids_str.split(',')] if voucher_ids_str else []
            order = dao.create_order_from_cart(
                user_id=current_user.id,
                restaurant_id=restaurant_id,
                cart_data=restaurant_cart,
                delivery_address=delivery_address,
                note=note,
                subtotal=subtotal,
                shipping_fee=shipping_fee,
                discount=discount_amount,
                voucher_ids=voucher_ids,
                initial_status=OrderState.UNPAID,
                delivery_lat=user_lat,
                delivery_lng=user_lng,
            )

        except Exception as e:
            flash(f'Đã có lỗi xảy ra khi tạo đơn hàng: {e}', 'danger')
            return redirect(url_for('checkout', restaurant_id=restaurant_id))

        # 3. Xử lý theo phương thức thanh toán

        if payment_method == 'vnpay':
            payment = dao.create_payment_record(order=order, payment_method='momo')
            pay_url = dao.create_momo_payment_request(payment)

            if pay_url:
                del session['cart'][restaurant_id_str]
                session.modified = True
                return redirect(pay_url)
            else:
                flash('Không thể tạo thanh toán MoMo. Vui lòng thử lại hoặc chọn phương thức khác.', 'danger')
                # (Tùy chọn) Có thể xóa đơn hàng vừa tạo hoặc để đó cho người dùng thử lại
                return redirect(url_for('checkout', restaurant_id=restaurant_id))

    # --- XỬ LÝ GET REQUEST  ---
    all_valid_vouchers = dao.get_valid_vouchers(restaurant_id, subtotal)
    shipping_vouchers_data = []
    shop_vouchers_data = []
    for v in all_valid_vouchers:
        voucher_dict = {"id": v.id, "code": v.code, "name": v.name, "description": v.description, "percent": v.percent,
                        "limit": v.limit, "max": v.max, "min": v.min}
        if 'FREESHIP' in v.code.upper():
            shipping_vouchers_data.append(voucher_dict)
        else:
            shop_vouchers_data.append(voucher_dict)

    return render_template('User/Order_Pay.html',
                           restaurant=restaurant,
                           cart_items=restaurant_cart['items'],
                           subtotal=subtotal,
                           delivery_time=delivery_time,
                           distance_km=distance_km,
                           shipping_fee=shipping_fee,
                           shipping_vouchers=shipping_vouchers_data,
                           shop_vouchers=shop_vouchers_data)

@app.route('/api/apply-voucher', methods=['POST'])
@login_required
def apply_voucher_api():
    data = request.json
    voucher_code = data.get('voucher_code', '')
    restaurant_id = data.get('restaurant_id')
    subtotal = data.get('subtotal')

    if not all([voucher_code, restaurant_id, subtotal]):
        return jsonify({'success': False, 'message': 'Dữ liệu không hợp lệ.'}), 400

    result = dao.apply_voucher(voucher_code, restaurant_id, subtotal)
    return jsonify(result)

@app.route('/track-order/<int:order_id>')
@login_required
def track_order_page(order_id):
    """
    Hiển thị trang theo dõi trạng thái đơn hàng theo thời gian thực.
    """
    # 1. Lấy thông tin chi tiết đơn hàng từ DAO
    order = dao.get_order_details_by_id(order_id)

    # 2. Kiểm tra xem đơn hàng có tồn tại không
    if not order:
        flash("Đơn hàng không tồn tại!", "danger")
        return redirect(url_for('index'))

    # 3. KIỂM TRA QUYỀN TRUY CẬP
    if current_user.id != order.user_id:
        flash("Bạn không có quyền xem đơn hàng này.", "danger")
        return redirect(url_for('index'))

    # 4. Nếu tất cả kiểm tra đều qua, hiển thị trang
    return render_template('track_order.html', order=order)
import admin

# 3.3.10 Module VNPay, chatbot
@app.route('/momo/confirm-payment/<int:payment_id>', methods=['POST'])
def momo_ipn_handler(payment_id):
    """
    Lắng nghe kết quả giao dịch từ MoMo (IPN - Instant Payment Notification).
    """
    response_data = request.get_json()


    payment = Payment.query.get(payment_id)
    if not payment:
        # Không tìm thấy payment, trả lỗi để MoMo không gọi lại nữa
        return jsonify({"status": "error", "message": "Payment not found"}), 404

    if response_data.get('resultCode') == 0 and payment.order.order_status.value == OrderState.UNPAID.value:
        # Thanh toán thành công
        payment.payment_status = PaymentStatus.PAID
        payment.order.order_status = OrderState.PENDING
        db.session.commit()

        order = payment.order
        daily_order_number = dao.count_orders_for_restaurant_today(order.restaurant_id)
        socketio.emit('new_order', {
            'order_id': order.id,
            'daily_order_number': daily_order_number,
            'total': "{:,.0f}đ".format(order.total),
            'customer_name': order.user.name
        }, room=f'restaurant_{order.restaurant_id}')

        print(f"Thanh toán {payment_id} đã được xác nhận thành công.")
    else:
        # Thanh toán thất bại
        payment.payment_status = PaymentStatus.FAILED
        db.session.commit()
        print(f"Thanh toán {payment_id} thất bại. Lý do: {response_data.get('message')}")

    # Phải trả về response với status 204 để MoMo biết đã nhận được
    return '', 204

@app.route('/my-active-orders')
@login_required
def active_orders_page():
    active_orders = dao.get_active_orders_for_user(current_user.id)
    return render_template('active_orders.html', orders=active_orders)

#xử lý thông báo nhà hàng
@socketio.on('connect')
def handle_connect():
    # Chỉ xử lý nếu người dùng đã đăng nhập và là nhà hàng
    if current_user.is_authenticated and current_user.role == UserRole.RESTAURANT:
        restaurant_id = session.get('restaurant_id')
        if restaurant_id:
            room_name = f'restaurant_{restaurant_id}'
            join_room(room_name)
            print(f"Restaurant {restaurant_id} has connected and joined room '{room_name}'")



@app.route('/api/chat', methods=['POST'])
def handle_chat():
    data = request.get_json()
    user_message = data.get('message')

    if not user_message:
        return jsonify({'error': 'Không có tin nhắn nào được gửi.'}), 400

    # 1. Lấy lịch sử chat hiện có từ session (hoặc tạo list rỗng nếu chưa có)
    chat_history = session.get('chat_history', [])

    # 2. Thêm tin nhắn của người dùng vào lịch sử
    chat_history.append({'sender': 'user', 'text': user_message})

    # 3. Gọi hàm DAO để lấy phản hồi từ AI
    ai_response = dao.call_gemini_api(user_message)

    # 4. Thêm phản hồi của AI vào lịch sử
    chat_history.append({'sender': 'assistant', 'text': ai_response})

    # 5. Lưu lại lịch sử đã cập nhật vào session
    session['chat_history'] = chat_history
    session.modified = True # Đảm bảo session được lưu

    # 6. Trả về chỉ câu trả lời mới nhất cho frontend
    return jsonify({'reply': ai_response})
from __init__ import socketio
if __name__ == '__main__':
    with app.app_context():

        import admin
        # app.run(debug=True)
        socketio.run(app, debug=True,port=5001)
