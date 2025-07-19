import datetime
from sqlalchemy import (Column, Integer, String, Boolean, Float, ForeignKey,
                        Enum, DateTime, Time, JSON)
from sqlalchemy.orm import relationship
from flask_login import UserMixin
from enum import Enum as PyEnum
from __init__ import db, app


class UserRole(PyEnum):
    USER = 'user'
    RESTAURANT = 'restaurant'
    ADMIN = 'admin'


class User(db.Model, UserMixin):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    email = Column(String(50), nullable=False, unique=True)
    phone = Column(String(10), unique=True, index=True)
    password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.USER)
    active = Column(Boolean, default=True)
    created_date = Column(DateTime, default=datetime.datetime.now)

    restaurants_owned = relationship('Restaurant', backref='user', lazy=True)
    orders = relationship('Order', backref='user', lazy=True)
    reviews = relationship('Review', backref='user', lazy=True)
    carts = relationship('Cart', backref='user', lazy=True)


# 3. Bảng trung gian FavoriteRestaurants
# Lưu ý: Với các bảng phụ (association table) được tạo bằng db.Table,
# ta vẫn cần cung cấp tên bảng một cách tường minh.
favorite_restaurants = db.Table('favorite_restaurants',
                                Column('user_id', Integer, ForeignKey('user.id'), primary_key=True),
                                Column('restaurant_id', Integer, ForeignKey('restaurant.id'), primary_key=True)
                                )


class Category(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    image = Column(String(100), default="https://res.cloudinary.com/dq2jtbrda/image/upload/v1752904668/randomfood_tfdwhd.jpg")

    # Mối quan hệ này cho phép từ một Category, bạn có thể truy cập
    # danh sách các nhà hàng thuộc về nó (ví dụ: category.restaurants)
    restaurants = relationship('Restaurant', back_populates='category', lazy='dynamic')


class Restaurant(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    owner_user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    category_id = Column(Integer, ForeignKey(Category.id), nullable=True)
    restaurant_name = Column(String(50), nullable=False)
    address = Column(String(100))
    email = Column(String(50), unique=True)
    description = Column(String(100))
    image = Column(String(100),
                   default='https://res.cloudinary.com/dxxwcby8l/image/upload/v1647056401/ipmsmnxjydrhpo21xrd8.jpg')
    open_time = Column(Time)
    close_time = Column(Time)
    status = Column(Boolean, default=True)
    active = Column(Boolean, default=False)

    created_date = Column(DateTime, default=datetime.datetime.now)

    # Relationships
    category = relationship('Category', back_populates='restaurants')

    dish_groups = relationship('DishGroup', backref='restaurant', lazy='dynamic')

    favorited_by_users = relationship('User', secondary=favorite_restaurants, lazy='subquery',
                                      backref=db.backref('favorite_restaurants', lazy=True))

    dishes = relationship('Dish', backref='restaurant', lazy=True)
    orders = relationship('Order', backref='restaurant', lazy=True)
    reviews = relationship('Review', backref='restaurant', lazy=True)
    carts = relationship('Cart', backref='restaurant', lazy=True)


class DishGroup(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    restaurant_id = Column(Integer, ForeignKey(Restaurant.id), nullable=False)
    dishes = relationship('Dish', back_populates='group', lazy='dynamic')


class Dish(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    restaurant_id = Column(Integer, ForeignKey(Restaurant.id), nullable=False, index=True)
    dish_group_id = Column(Integer, ForeignKey(DishGroup.id), nullable=True)
    name = Column(String(50), nullable=False)
    description = Column(String(100))
    price = Column(Float, nullable=False, default=0)
    image = Column(String(100))

    group = relationship('DishGroup', back_populates='dishes')
    option_groups = relationship('DishOptionGroup', backref='dish', lazy=True)


class DishOptionGroup(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    dish_id = Column(Integer, ForeignKey(Dish.id), nullable=False)
    name = Column(String(50), nullable=False)
    mandatory = Column(Boolean, default=False)
    max = Column(Integer)
    options = relationship('DishOption', backref='dish_option_group', lazy=True)


class Cart(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    restaurant_id = Column(Integer, ForeignKey(Restaurant.id), nullable=False)
    items = relationship('CartItem', backref='cart', lazy=True, cascade="all, delete-orphan")


class CartItem(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    cart_id = Column(Integer, ForeignKey(Cart.id), nullable=False)
    dish_id = Column(Integer, ForeignKey(Dish.id), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)

    dish = relationship('Dish', lazy='joined')
    selected_options = relationship('DishOption', secondary='cart_item_option', backref='cart_item',
                                    lazy='joined'
                                    )


class DishOption(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    option_group_id = Column(Integer, ForeignKey(DishOptionGroup.id), nullable=False)
    name = Column(String(50), nullable=False)
    price = Column(Float, default=0)


class CartItemOption(db.Model):
    cart_item_id = Column(Integer, ForeignKey(CartItem.id), primary_key=True, nullable=False)
    dish_option_id = Column(Integer, ForeignKey(DishOption.id), primary_key=True, nullable=False)
    quantity = Column(Integer, default=1)


class OrderState(PyEnum):
    PENDING = "Pending"
    CONFIRMED = "Confirmed"
    DELIVERING = "Delivering"
    COMPLETED = "Completed"


class Order(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False, index=True)
    restaurant_id = Column(Integer, ForeignKey(Restaurant.id), nullable=False, index=True)
    order_date = Column(DateTime, default=datetime.datetime.now)
    subtotal = Column(Float, nullable=False)  # tổng tiền
    discount = Column(Float, default=0)  # giảm giá
    total = Column(Float, nullable=False)  # thành tiền
    delivery_address = Column(String(50), nullable=False)
    note = Column(String(100))
    order_status = Column(Enum(OrderState), default=OrderState.PENDING, nullable=False)

    details = relationship('OrderDetail', backref='order', lazy=True)
    review = relationship('Review', backref='order', uselist=False, cascade="all, delete-orphan")


class OrderDetail(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey(Order.id), nullable=False, index=True)
    dish_id = Column(Integer, ForeignKey(Dish.id), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    dish_name = Column(String(255))
    selected_options_luc_dat = Column(JSON)

    dish = relationship('Dish', lazy='joined')


class Review(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False, index=True)
    restaurant_id = Column(Integer, ForeignKey(Restaurant.id), nullable=False, index=True)
    order_id = Column(Integer, ForeignKey(Order.id), nullable=False, unique=True)
    star = Column(Integer, nullable=False)
    comment = Column(String(1000))
    date = Column(DateTime, default=datetime.datetime.now)


class Voucher(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), nullable=False, unique=True)
    name = Column(String(50))
    description = Column(String(500))
    percent = Column(Float)
    limit = Column(Float)
    min = Column(Float)
    max = Column(Float)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    active = Column(Boolean, default=True)


voucher_applied = db.Table('voucher_applied',
                           Column('order_id', Integer, ForeignKey('order.id'), primary_key=True),
                           Column('voucher_id', Integer, ForeignKey('voucher.id'), primary_key=True)
                           )

Order.vouchers = relationship('Voucher', secondary=voucher_applied, lazy='subquery',
                              backref=db.backref('orders_applied', lazy=True))

if __name__ == '__main__':
    # Lệnh này cần chạy trong ngữ cảnh của ứng dụng Flask
    with app.app_context():
        db.drop_all()
        db.create_all()
        db.session.commit()

        # --- Bắt đầu tạo dữ liệu ---

        # 1. TẠO NGƯỜI DÙNG
        # Sử dụng werkzeug để băm mật khẩu, an toàn hơn MD5 rất nhiều.
        # Cần: pip install Werkzeug
        import hashlib  # Sử dụng thuật toán băm

        # Tạo người dùng Admin
        admin_user = User(name='Admin Master', email='admin@ofood.com', phone='0900000000',
                          password=hashlib.md5('123456'.encode('utf-8')), role=UserRole.ADMIN)

        # Tạo các chủ nhà hàng
        owner1 = User(name='Anh Bảy Cơm Tấm', email='owner1@ofood.com', phone='0901111111',
                      password=hashlib.md5('123456'.encode('utf-8')), role=UserRole.RESTAURANT)
        owner2 = User(name='Chị Mười Bún Bò', email='owner2@ofood.com', phone='0902222222',
                      password=hashlib.md5('123456'.encode('utf-8')), role=UserRole.RESTAURANT)

        # Tạo các khách hàng
        customer1 = User(name='Khách Hàng A', email='customer1@email.com', phone='0981112222',
                         password=hashlib.md5('123456'.encode('utf-8')), role=UserRole.USER)
        customer2 = User(name='Khách Hàng B', email='customer2@email.com', phone='0982223333',
                         password=hashlib.md5('123456'.encode('utf-8')), role=UserRole.USER)

        db.session.add_all([admin_user, owner1, owner2, customer1, customer2])
        db.session.commit()

        # 2. TẠO NHÀ HÀNG
        restaurant1 = Restaurant(owner_user_id=owner1.id, restaurant_name='Cơm Tấm Bảy Đời',
                                 address='123 Đường Cơm, Phường 1, Quận 1, TP.HCM',
                                 email='comtambaydoi@email.com', description='Cơm tấm gia truyền, sườn ướp đậm đà.')
        restaurant2 = Restaurant(owner_user_id=owner2.id, restaurant_name='Bún Bò Mười Ngon',
                                 address='456 Đường Bún, Phường 2, Quận 3, TP.HCM',
                                 email='bunbomuoi@email.com', description='Bún bò Huế chuẩn vị, nước lèo thanh ngọt.')

        # Khách hàng yêu thích nhà hàng
        customer1.favorite_restaurants.append(restaurant1)
        customer1.favorite_restaurants.append(restaurant2)
        customer2.favorite_restaurants.append(restaurant2)

        db.session.add_all([restaurant1, restaurant2])
        db.session.commit()

        # 3. TẠO MÓN ĂN VÀ TÙY CHỌN
        # Món ăn cho nhà hàng 1
        dish1_1 = Dish(restaurant_id=restaurant1.id, name='Cơm tấm sườn', price=35000)
        dish1_2 = Dish(restaurant_id=restaurant1.id, name='Cơm tấm bì chả', price=30000)
        dish1_3 = Dish(restaurant_id=restaurant1.id, name='Canh khổ qua', price=10000)

        # Món ăn cho nhà hàng 2
        dish2_1 = Dish(restaurant_id=restaurant2.id, name='Bún bò đặc biệt', price=55000)
        dish2_2 = Dish(restaurant_id=restaurant2.id, name='Bún bò giò nạm', price=45000)

        db.session.add_all([dish1_1, dish1_2, dish1_3, dish2_1, dish2_2])
        db.session.commit()

        # Tùy chọn cho món ăn (ví dụ: thêm trứng cho cơm tấm)
        option_group1 = DishOptionGroup(dish_id=dish1_1.id, name='Thêm topping', mandatory=False)
        db.session.add(option_group1)
        db.session.commit()

        option1_1 = DishOption(option_group_id=option_group1.id, name='Trứng ốp la', price=5000)
        option1_2 = DishOption(option_group_id=option_group1.id, name='Lạp xưởng', price=7000)
        db.session.add_all([option1_1, option1_2])
        db.session.commit()

        # 4. TẠO VOUCHER
        voucher1 = Voucher(code='GIAM10K', name='Giảm 10k cho đơn từ 50k', percent=0, limit=10000, min=50000, max=10000,
                           start_date=datetime.datetime.now(),
                           end_date=datetime.datetime.now() + datetime.timedelta(days=30))
        voucher2 = Voucher(code='FREESHIP', name='Miễn phí vận chuyển', percent=0, limit=15000, min=30000, max=15000,
                           start_date=datetime.datetime.now(),
                           end_date=datetime.datetime.now() + datetime.timedelta(days=30))
        db.session.add_all([voucher1, voucher2])
        db.session.commit()

        # 5. TẠO ĐƠN HÀNG VÀ CHI TIẾT ĐƠN HÀNG
        # Đơn hàng 1 của customer1 tại restaurant1
        order1_subtotal = dish1_1.price + dish1_3.price  # Cơm tấm sườn + Canh khổ qua
        order1_discount = voucher1.limit
        order1_total = order1_subtotal - order1_discount

        order1 = Order(user_id=customer1.id, restaurant_id=restaurant1.id, subtotal=order1_subtotal,
                       discount=order1_discount, total=order1_total, delivery_address='Nhà A, Chung cư Z, TP.HCM',
                       order_status=OrderState.COMPLETED)
        order1.vouchers.append(voucher1)  # Áp dụng voucher
        db.session.add(order1)
        db.session.commit()

        detail1_1 = OrderDetail(order_id=order1.id, dish_id=dish1_1.id, quantity=1, price=dish1_1.price,
                                dish_name=dish1_1.name, selected_options_luc_dat={})
        detail1_2 = OrderDetail(order_id=order1.id, dish_id=dish1_3.id, quantity=1, price=dish1_3.price,
                                dish_name=dish1_3.name, selected_options_luc_dat={})
        db.session.add_all([detail1_1, detail1_2])
        db.session.commit()

        # Đơn hàng 2 của customer2 tại restaurant2
        order2_subtotal = dish2_1.price * 2  # 2 tô bún bò đặc biệt
        order2_total = order2_subtotal  # Không có giảm giá
        order2 = Order(user_id=customer2.id, restaurant_id=restaurant2.id, subtotal=order2_subtotal,
                       total=order2_total, delivery_address='100 Nguyễn Trãi, Quận 5, TP.HCM',
                       order_status=OrderState.DELIVERING)
        db.session.add(order2)
        db.session.commit()

        detail2_1 = OrderDetail(order_id=order2.id, dish_id=dish2_1.id, quantity=2, price=dish2_1.price,
                                dish_name=dish2_1.name, selected_options_luc_dat={})
        db.session.add(detail2_1)
        db.session.commit()

        # 6. TẠO ĐÁNH GIÁ (REVIEW)
        # Chỉ những đơn hàng đã COMPLETED mới có thể có review
        review1 = Review(user_id=order1.user_id, restaurant_id=order1.restaurant_id, order_id=order1.id,
                         star=5, comment='Cơm tấm ngon, giao hàng nhanh. Sẽ ủng hộ tiếp!')
        db.session.add(review1)
        db.session.commit()

        # 1. Tạo các Category
        cat_com = Category(name='Cơm')
        cat_trasua = Category(name='Trà sữa')
        db.session.add_all([cat_com, cat_trasua])
        db.session.commit()

        # 2. Gán Category cho một nhà hàng
        # Giả sử bạn đã có một nhà hàng tên `restaurant1`
        # Gán trực tiếp đối tượng Category, không dùng .append() nữa
        restaurant1.category = cat_com
        db.session.commit()

        # 3. Tạo DishGroup cho nhà hàng đó
        group_com_chinh = DishGroup(name='Món Cơm Chính', restaurant_id=restaurant1.id)
        group_canh = DishGroup(name='Các Món Canh', restaurant_id=restaurant1.id)
        db.session.add_all([group_com_chinh, group_canh])
        db.session.commit()

        # 4. Tạo Món ăn và gán vào DishGroup
        com_tam = Dish(name='Cơm tấm đặc biệt', price=35000, restaurant_id=restaurant1.id, group=group_com_chinh)
        canh_kho_qua = Dish(name='Canh khổ qua', price=10000, restaurant_id=restaurant1.id, group=group_canh)
        db.session.add_all([com_tam, canh_kho_qua])
        db.session.commit()

        print("--- TẠO DỮ LIỆU THỬ NGHIỆM THÀNH CÔNG ---")
