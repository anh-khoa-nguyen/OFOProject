import datetime
from datetime import time
from sqlalchemy import (Column, Integer, String, Boolean, Float, ForeignKey,
                        Enum, DateTime, Time, JSON, Numeric)
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
    avatar = Column(String(100), default='https://res.cloudinary.com/dxxwcby8l/image/upload/v1647056401/ipmsmnxjydrhpo21xrd8.jpg')
    active = Column(Boolean, default=True)
    created_date = Column(DateTime, default=datetime.datetime.now)

    restaurants_owned = relationship('Restaurant', backref='user', lazy=True)
    orders = relationship('Order', backref='user', lazy=True)
    reviews = relationship('Review', backref='user', lazy=True)
    # carts = relationship('Cart', backref='user', lazy=True)


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
    image = Column(String(400), default="https://res.cloudinary.com/dq2jtbrda/image/upload/v1752904668/randomfood_tfdwhd.jpg")

    # Mối quan hệ này cho phép từ một Category, bạn có thể truy cập
    # danh sách các nhà hàng thuộc về nó (ví dụ: category.restaurants)
    restaurants = relationship('Restaurant', back_populates='category', lazy='dynamic')


class Restaurant(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    owner_user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    category_id = Column(Integer, ForeignKey(Category.id), nullable=True)
    restaurant_name = Column(String(50), nullable=False)
    address = Column(String(100))
    lat = Column(Numeric(10, 7), nullable=True)
    lng = Column(Numeric(10, 7), nullable=True)
    description = Column(String(100))
    image = Column(String(500),
                   default='https://res.cloudinary.com/dxxwcby8l/image/upload/v1647056401/ipmsmnxjydrhpo21xrd8.jpg')
    open_time = Column(Time)
    close_time = Column(Time)
    status = Column(Boolean, default=True)
    active = Column(Boolean, default=False)
    star_average = Column(Float, default=0)

    created_date = Column(DateTime, default=datetime.datetime.now)

    # Relationships
    category = relationship('Category', back_populates='restaurants')

    dish_groups = relationship('DishGroup', back_populates='restaurant', lazy='subquery')

    favorited_by_users = relationship('User', secondary=favorite_restaurants, lazy='subquery',
                                      backref=db.backref('favorite_restaurants', lazy='dynamic'))

    dishes = relationship('Dish', backref='restaurant', lazy=True)
    orders = relationship('Order', backref='restaurant', lazy=True)
    reviews = relationship('Review', backref='restaurant', lazy=True)
    # carts = relationship('Cart', backref='restaurant', lazy=True)


class DishGroup(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    restaurant_id = Column(Integer, ForeignKey(Restaurant.id), nullable=False)

    restaurant = relationship('Restaurant', back_populates='dish_groups')
    dishes = relationship('Dish', back_populates='group', lazy='subquery')


class Dish(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    restaurant_id = Column(Integer, ForeignKey(Restaurant.id), nullable=False, index=True)
    dish_group_id = Column(Integer, ForeignKey(DishGroup.id), nullable=True)
    name = Column(String(50), nullable=False)
    description = Column(String(255))
    price = Column(Float, nullable=False, default=0)
    active = Column(Boolean, default=True)
    image = Column(String(100), default="https://res.cloudinary.com/dq2jtbrda/image/upload/v1752912326/tocotrachieu_uqllag.webp")

    group = relationship('DishGroup', back_populates='dishes')
    option_groups = relationship('DishOptionGroup',
                                 secondary='dish_has_option_groups',
                                 lazy='subquery',
                                 backref=db.backref('dishes', lazy=True))

dish_has_option_groups = db.Table('dish_has_option_groups',
    db.Column('dish_id', Integer, ForeignKey('dish.id'), primary_key=True),
    db.Column('dish_option_group_id', Integer, ForeignKey('dish_option_group.id'), primary_key=True)
)

class DishOptionGroup(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    restaurant_id = Column(Integer, ForeignKey(Restaurant.id), nullable=False, index=True)
    name = Column(String(50), nullable=False)
    mandatory = Column(Boolean, default=False)
    max = Column(Integer)
    options = relationship(
        'DishOption',
        back_populates='group',          # <-- Dùng back_populates thay cho backref
        cascade="all, delete-orphan",    # <-- Thêm cascade để xóa theo
        lazy='subquery'                   # <-- Dùng lazy='dynamic' cho hiệu quả
    )
class DishOption(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    option_group_id = Column(Integer, ForeignKey(DishOptionGroup.id), nullable=False)
    name = Column(String(50), nullable=False)
    price = Column(Float, default=0)
    group = relationship('DishOptionGroup', back_populates='options')



# class Cart(db.Model):
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     user_id = Column(Integer, ForeignKey(User.id), nullable=False)
#     restaurant_id = Column(Integer, ForeignKey(Restaurant.id), nullable=False)
#     items = relationship('CartItem', backref='cart', lazy=True, cascade="all, delete-orphan")

# class CartItem(db.Model):
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     cart_id = Column(Integer, ForeignKey(Cart.id), nullable=False)
#     dish_id = Column(Integer, ForeignKey(Dish.id), nullable=False)
#     quantity = Column(Integer, nullable=False, default=1)
#
#     dish = relationship('Dish', lazy='joined')
#     selected_options = relationship('DishOption', secondary='cart_item_option', backref='cart_item',
#                                     lazy='joined'
#                                     )
#
# class CartItemOption(db.Model):
#     cart_item_id = Column(Integer, ForeignKey(CartItem.id), primary_key=True, nullable=False)
#     dish_option_id = Column(Integer, ForeignKey(DishOption.id), primary_key=True, nullable=False)
#     quantity = Column(Integer, default=1)


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
    image = Column(String(1000))
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
    with app.app_context():
        from sqlalchemy import text

        # --- SỬA LỖI Ở ĐÂY: Sử dụng một kết nối duy nhất từ engine ---
        with db.engine.connect() as connection:
            # Bắt đầu một transaction
            with connection.begin():
                print("--- Tạm thời vô hiệu hóa Foreign Key Checks ---")
                connection.execute(text('SET FOREIGN_KEY_CHECKS=0;'))

                print("--- Bắt đầu xóa tất cả các bảng (drop_all) ---")
                # Yêu cầu drop_all sử dụng kết nối này
                db.metadata.drop_all(bind=connection)
                print("--- Xóa bảng thành công ---")

                print("--- Bắt đầu tạo tất cả các bảng (create_all) ---")
                # Yêu cầu create_all sử dụng kết nối này
                db.metadata.create_all(bind=connection)
                print("--- Tạo bảng thành công ---")

                print("--- Kích hoạt lại Foreign Key Checks ---")
                connection.execute(text('SET FOREIGN_KEY_CHECKS=1;'))

        # Sau khi schema đã ổn định, bắt đầu thêm dữ liệu
        print("\n--- Bắt đầu tạo dữ liệu ---")

        # --- Bắt đầu tạo dữ liệu ---

        # 1. TẠO NGƯỜI DÙNG
        import hashlib  # Sử dụng thuật toán băm

        # Tạo người dùng Admin
        admin_user = User(name='Admin Master', email='admin@ofood.com', phone='0900000000',
                          password=str(hashlib.md5('123456'.encode('utf-8')).hexdigest()), role=UserRole.ADMIN)

        # Tạo các chủ nhà hàng
        owner1 = User(name='Anh Bảy Cơm Tấm', email='owner1@ofood.com', phone='0901111111',
                      password=str(hashlib.md5('123456'.encode('utf-8')).hexdigest()), role=UserRole.RESTAURANT)
        owner2 = User(name='Chị Mười Bún Bò', email='owner2@ofood.com', phone='0902222222',
                      password=str(hashlib.md5('123456'.encode('utf-8')).hexdigest()), role=UserRole.RESTAURANT)

        # Tạo các khách hàng
        customer1 = User(name='Khách Hàng A', email='customer1@email.com', phone='0981112222',
                         password=str(hashlib.md5('123456'.encode('utf-8')).hexdigest()), role=UserRole.USER)
        customer2 = User(name='Khách Hàng B', email='customer2@email.com', phone='0982223333',
                         password=str(hashlib.md5('123456'.encode('utf-8')).hexdigest()), role=UserRole.USER)
        customer3 = User(name='Khách Hàng C', email='customer3@email.com', phone='0982223331',
                         password=str(hashlib.md5('123456'.encode('utf-8')).hexdigest()), role=UserRole.USER)
        customer6 = User(name='Khách Hàng D', email='customer4@email.com', phone='0982223334',
                         password=str(hashlib.md5('123456'.encode('utf-8')).hexdigest()), role=UserRole.USER)
        customer4 = User(name='Khách Hàng E', email='customer5@email.com', phone='0982223335',
                         password=str(hashlib.md5('123456'.encode('utf-8')).hexdigest()), role=UserRole.USER)
        customer5 = User(name='Khách Hàng F', email='customer6@email.com', phone='0982223336',
                         password=str(hashlib.md5('123456'.encode('utf-8')).hexdigest()), role=UserRole.USER)

        db.session.add_all([admin_user, owner1, owner2, customer1, customer2,customer3,customer4,customer5,customer6])
        db.session.commit()

        #=====================================================================================================================
        # 1. Tạo các Category
        cat_hutieu = Category(name='Hủ tiếu',
                              image='https://res.cloudinary.com/dq2jtbrda/image/upload/v1752910881/hutieu_dashlv.jpg')
        cat_trasua = Category(name='Trà sữa',
                              image='https://res.cloudinary.com/dq2jtbrda/image/upload/v1752910879/trasua_gnipc9.jpg')
        cat_thucannhanh = Category(name='Thức ăn nhanh',
                                   image='https://res.cloudinary.com/dq2jtbrda/image/upload/v1752910878/thucannhanh_iwpo6l.jpg')
        cat_comtam = Category(name='Cơm tấm',
                              image='https://res.cloudinary.com/dq2jtbrda/image/upload/v1752910878/comtam_rhgbr4.webp')
        cat_banhmi = Category(name='Bánh mì',
                              image='https://res.cloudinary.com/dq2jtbrda/image/upload/v1752910877/banhmi_psbpiy.jpg')
        cat_chao = Category(name='Cháo',
                            image='https://res.cloudinary.com/dq2jtbrda/image/upload/v1752910878/chao_qyei6t.jpg')
        cat_thitga = Category(name='Thịt gà',
                              image='https://res.cloudinary.com/dq2jtbrda/image/upload/v1752910878/thitga_fb0zwg.webp')
        cat_pizza = Category(name='Pizza',
                             image='https://res.cloudinary.com/dq2jtbrda/image/upload/v1752910878/pizza_pchnus.webp')
        cat_amthucviet = Category(name='Ẩm thực Việt',
                             image='https://res.cloudinary.com/dbb1oslnw/image/upload/v1753188270/ATV_kk1dxf.jpg')
        cat_monnhat = Category(name='Món Nhật',
                                  image='https://res.cloudinary.com/dbb1oslnw/image/upload/v1753188466/istockphoto-917919440-612x612_etf1zp.jpg')
        cat_cafe  = Category(name='Cafe',
                                   image='https://res.cloudinary.com/dbb1oslnw/image/upload/v1753188962/omce-coffee-aivivu-1_ctggu5.jpg')



        db.session.add_all(
            [cat_hutieu, cat_trasua, cat_thucannhanh, cat_comtam, cat_banhmi, cat_chao, cat_thitga, cat_pizza,cat_amthucviet,cat_monnhat,cat_cafe])
        db.session.commit()

        #=====================================================================================================================
        # 2. TẠO NHÀ HÀNG (PROFILE)
        restaurant1 = Restaurant(owner_user_id=owner1.id,
                                 restaurant_name='Mì Trộn Tên Lửa - CMT8',
                                 address='111 Cách Mạng Tháng Tám, P. 1, Q. 3, TP.HCM',
                                 description='Mì trộn độc đáo với các loại sốt nhà làm.',
                                 image='https://res.cloudinary.com/dq2jtbrda/image/upload/v1752910914/mitron_bbzzqc.jpg',
                                 lat =10.773291135000022,
                                 lng =106.68979721600004,
                                 # Thêm giờ mở/đóng cửa
                                 open_time=time(10, 0),  # 10:00 AM
                                 close_time=time(22, 0),
                                 active=True)  # 10:00 PM,

        restaurant2 = Restaurant(owner_user_id=owner2.id,
                                 restaurant_name='Tiệm Cơm Nhà Trộn - Phú Nhuận',
                                 address='222 Phan Xích Long, P. 2, Q. Phú Nhuận, TP.HCM',
                                 description='Cơm trộn Hàn Quốc chuẩn vị cho giới trẻ.',
                                 image='https://res.cloudinary.com/dq2jtbrda/image/upload/v1752910914/comtron_qhxxer.jpg',
                                 lat =10.834618,
                                 lng =106.665187,
                                 # Thêm giờ mở/đóng cửa
                                 open_time=time(11, 0),  # 11:00 AM
                                 close_time=time(21, 30),
                                 active=True)  # 09:30 PM

        restaurant3 = Restaurant(owner_user_id=owner2.id,
                                 restaurant_name='Jollibee - EC Tô Hiến Thành',
                                 address='333 Tô Hiến Thành, P. 13, Q. 10, TP.HCM',
                                 description='Gà giòn vui vẻ, Mì Ý sốt bò bằm.',
                                 image='https://res.cloudinary.com/dq2jtbrda/image/upload/v1752910914/garan_mzz4tb.webp',
                                 lat=10.77735356900007,
                                 lng=106.66494351700004,
                                 # Thêm giờ mở/đóng cửa
                                 open_time=time(9, 0),  # 09:00 AM
                                 close_time=time(22, 45),
                                 active=True)  # 10:45 PM

        restaurant4 = Restaurant(owner_user_id=owner1.id,
                                 restaurant_name='Bánh Mì Huỳnh Gia - Lê Văn Lương',
                                 address='444 Lê Văn Lương, P. Tân Hưng, Q. 7, TP.HCM',
                                 description='Bánh mì heo quay da giòn trứ danh.',
                                 image='https://res.cloudinary.com/dq2jtbrda/image/upload/v1752910913/banhmi_w70ph8.webp',
                                 lat=10.736429194000038,
                                 lng=106.70292244500007,
                                 # Thêm giờ mở/đóng cửa
                                 open_time=time(6, 30),  # 06:30 AM
                                 close_time=time(20, 0),
                                 active=True)  # 08:00 PM
        restaurant5 = Restaurant(owner_user_id=owner1.id,
                                 restaurant_name='Bún Bò Huế O Cương Chú Điệp',
                                 address='242/12 Nguyễn Thiện Thuật, P. 3, Q. 3, TP.HCM',
                                 description='Bún bò Huế đậm đà hương vị truyền thống.',
                                 image='https://res.cloudinary.com/dbb1oslnw/image/upload/v1753189389/bunbohue_tph_09_afz7md.jpg',
                                 lat=10.773291,
                                 lng=106.689797,
                                 # Thêm giờ mở/đóng cửa
                                 open_time=time(10, 0),  # 10:00 AM
                                 close_time=time(22, 0),
                                 active=True)  # 10:00 PM,
        restaurant6 = Restaurant(owner_user_id=owner2.id,
                                 restaurant_name='Cơm Tấm Ba Ghiền',
                                 address='84 Đặng Văn Ngữ, P. 10, Q. Phú Nhuận, TP.HCM',
                                 description='Sườn nướng mật ong trứ danh.',
                                 image='https://res.cloudinary.com/dbb1oslnw/image/upload/v1753190745/images_1_eqa8vc.jpg',
                                 lat=10.794850,
                                 lng=106.676250,
                                 # Thêm giờ mở/đóng cửa
                                 open_time=time(10, 0),  # 10:00 AM
                                 close_time=time(22, 0),
                                 active=True)
        restaurant7 = Restaurant(owner_user_id=owner2.id,
                                 restaurant_name='Phở Lệ - Nguyễn Trãi',
                                 address='413-415 Nguyễn Trãi, P. 7, Q. 5, TP.HCM',
                                 description='Tô phở đầy đặn, nước lèo ngọt thanh.',
                                 image='https://res.cloudinary.com/dbb1oslnw/image/upload/v1753190614/pho-le-sai-gon-01-1720501423_cb477g.jpg',
                                 lat=10.753580,
                                 lng=106.670050,
                                 # Thêm giờ mở/đóng cửa
                                 open_time=time(10, 0),  # 10:00 AM
                                 close_time=time(22, 0),
                                 active=True)
        restaurant8 = Restaurant(owner_user_id=owner1.id,
                                 restaurant_name='Gogi House - Quang Trung',
                                 address='1 Quang Trung, P. 11, Q. Gò Vấp, TP.HCM',
                                 description='Thịt nướng Hàn Quốc chuẩn vị.',
                                 image='https://res.cloudinary.com/dbb1oslnw/image/upload/v1753190899/images_pf5lrc.png',
                                 lat=10.832850,
                                 lng=106.665780,
                                 # Thêm giờ mở/đóng cửa
                                 open_time=time(10, 0),  # 10:00 AM
                                 close_time=time(22, 0),
                                 active=True)
        restaurant9 = Restaurant(owner_user_id=owner1.id,
                                 restaurant_name='Lẩu Dê 404 - Lê Văn Khương',
                                 address='404 Lê Văn Khương, P. Thới An, Q. 12, TP.HCM',
                                 description='Lẩu dê nóng hổi, thịt mềm.',
                                 image='https://res.cloudinary.com/dbb1oslnw/image/upload/v1753191068/images_2_xc7xlg.jpg',
                                 lat=10.868910,
                                 lng=106.641390,
                                 # Thêm giờ mở/đóng cửa
                                 open_time=time(10, 0),  # 10:00 AM
                                 close_time=time(22, 0),
                                 active=True)
        restaurant10 = Restaurant(owner_user_id=owner1.id,
                                 restaurant_name='Sushi Hokkaido Sachi - Vincom Thủ Đức',
                                 address='216 Võ Văn Ngân, P. Bình Thọ, TP. Thủ Đức, TP.HCM',
                                 description='Sushi và sashimi tươi ngon.',
                                 image='https://res.cloudinary.com/dbb1oslnw/image/upload/v1753191372/Hokkaido-sushi-1024x819_ewdbmq.jpg',
                                 lat=10.849930,
                                 lng=106.753740,
                                 # Thêm giờ mở/đóng cửa
                                 open_time=time(10, 0),  # 10:00 AM
                                 close_time=time(22, 0),
                                 active=True)
        restaurant11 = Restaurant(owner_user_id=owner1.id,
                                  restaurant_name='KFC - AEON Mall Bình Tân',
                                  address='Số 1 đường số 17A, P. Bình Trị Đông B, Q. Bình Tân, TP.HCM',
                                  description='Gà rán giòn tan, khoai tây chiên nóng hổi.',
                                  image='https://res.cloudinary.com/dbb1oslnw/image/upload/v1753191569/39wkPMS6pLZ4W8JSWEJYu2tnDaOBML9RGfxlqLNK_wutflb.webp',
                                  lat=10.747810,
                                  lng=106.605390,
                                  # Thêm giờ mở/đóng cửa
                                  open_time=time(10, 0),  # 10:00 AM
                                  close_time=time(22, 0),
                                  active=True)
        restaurant12 = Restaurant(owner_user_id=owner1.id,
                                  restaurant_name='The Coffee House - Phan Văn Trị',
                                  address='510 Phan Văn Trị, P. 7, Q. Gò Vấp, TP.HCM',
                                  description='Không gian yên tĩnh, cà phê đậm đà.',
                                  image='https://res.cloudinary.com/dbb1oslnw/image/upload/v1753191745/1614958720329-h%E1%BB%8Dc_b%E1%BB%95ng_c%C3%A1c_ch%C3%A2u_l%E1%BB%A5c_16_hpognh.png',
                                  lat=10.828540,
                                  lng=106.688920,
                                  # Thêm giờ mở/đóng cửa
                                  open_time=time(10, 0),  # 10:00 AM
                                  close_time=time(22, 0),
                                  active=True)
        restaurant13 = Restaurant(owner_user_id=owner1.id,
                                  restaurant_name='Bánh Canh Cua 14 - Hóc Môn',
                                  address='14 Song Hành, TT. Hóc Môn, Huyện Hóc Môn, TP.HCM',
                                  description='Bánh canh cua đặc quánh, topping đầy đủ.',
                                  image='https://res.cloudinary.com/dbb1oslnw/image/upload/v1753191938/15173065480_rlv9h1.jpg',
                                  lat=10.880120,
                                  lng=106.589450,
                                  # Thêm giờ mở/đóng cửa
                                  open_time=time(10, 0),  # 10:00 AM
                                  close_time=time(22, 0),
                                  active=True)
        restaurant14 = Restaurant(owner_user_id=owner1.id,
                                  restaurant_name='Pizza Hut - Co.opmart Thủ Đức',
                                  address='Km 9 Xa lộ Hà Nội, P. Hiệp Phú, TP. Thủ Đức, TP.HCM',
                                  description='Pizza viền phô mai béo ngậy.',
                                  image='https://res.cloudinary.com/dbb1oslnw/image/upload/v1753192265/Pizza-Hut-New-Logo-Design_ohmxk1.jpg',
                                  lat=10.849320,
                                  lng=106.770180,
                                  # Thêm giờ mở/đóng cửa
                                  open_time=time(10, 0),  # 10:00 AM
                                  close_time=time(22, 0),
                                  active=True)
        restaurant15 = Restaurant(owner_user_id=owner2.id,
                                  restaurant_name='Lẩu Nấm Ashima - Tú Xương',
                                  address='35A Tú Xương, P. Võ Thị Sáu, Q. 3, TP.HCM',
                                  description='Lẩu nấm thiên nhiên bổ dưỡng.',
                                  image='https://res.cloudinary.com/dbb1oslnw/image/upload/v1753192319/images_1_pd1fik.png',
                                  lat=10.781890,
                                  lng=106.689510,
                                  # Thêm giờ mở/đóng cửa
                                  open_time=time(10, 0),  # 10:00 AM
                                  close_time=time(22, 0),
                                  active=True)
        restaurant16 = Restaurant(owner_user_id=owner2.id,
                                  restaurant_name='Bò Tơ Củ Chi - Xuyên Á',
                                  address='Quốc lộ 22, Xã Tân Phú Trung, Huyện Củ Chi, TP.HCM',
                                  description='Đặc sản bò tơ Củ Chi chính gốc.',
                                  image='https://res.cloudinary.com/dbb1oslnw/image/upload/v1753192519/images_2_jtb47b.png',
                                  lat=10.915670,
                                  lng=106.558980,
                                  # Thêm giờ mở/đóng cửa
                                  open_time=time(10, 0),  # 10:00 AM
                                  close_time=time(22, 0),
                                  active=True)
        restaurant17 = Restaurant(owner_user_id=owner1.id,
                                  restaurant_name='Highlands Coffee - Gigamall',
                                  address='240-242 Phạm Văn Đồng, P. Hiệp Bình Chánh, TP. Thủ Đức, TP.HCM',
                                  description='Phin sữa đá và trà sen vàng nổi tiếng.',
                                  image='https://res.cloudinary.com/dbb1oslnw/image/upload/v1753192647/09160234_logo-highland-900x900_kvoocd.png',
                                  lat=10.828880,
                                  lng=106.720010,
                                  # Thêm giờ mở/đóng cửa
                                  open_time=time(10, 0),  # 10:00 AM
                                  close_time=time(22, 0),
                                  active=True)
        restaurant18 = Restaurant(owner_user_id=owner1.id,
                                  restaurant_name='Marukame Udon - Lý Tự Trọng',
                                  address='215-217 Lý Tự Trọng, P. Bến Thành, Q. 1, TP.HCM',
                                  description='Mì Udon sợi tươi làm tại chỗ.',
                                  image='https://res.cloudinary.com/dbb1oslnw/image/upload/v1753192761/images_3_my6zoo.jpg',
                                  lat=10.773820,
                                  lng=106.695740,
                                  # Thêm giờ mở/đóng cửa
                                  open_time=time(10, 0),  # 10:00 AM
                                  close_time=time(22, 0),
                                  active=True)
        restaurant19 = Restaurant(owner_user_id=owner1.id,
                                  restaurant_name='Bánh Xèo Ăn Là Ghiền',
                                  address='74 Sương Nguyệt Ánh, P. Bến Thành, Q. 1, TP.HCM',
                                  description='Bánh xèo giòn rụm, rau rừng tươi ngon.',
                                  image='https://res.cloudinary.com/dbb1oslnw/image/upload/v1753192883/images_4_uugpfd.jpg',
                                  lat=10.772560,
                                  lng=106.691890,
                                  # Thêm giờ mở/đóng cửa
                                  open_time=time(10, 0),  # 10:00 AM
                                  close_time=time(22, 0),
                                  active=True)



        #=====================================================================================================================
        # 3. KHÁCH YÊU THÍCH NHÀ HÀNG
        customer1.favorite_restaurants.append(restaurant1)
        customer1.favorite_restaurants.append(restaurant2)
        customer2.favorite_restaurants.append(restaurant3)

        db.session.add_all([restaurant1, restaurant2, restaurant3, restaurant4,restaurant5,restaurant6,restaurant7,restaurant8,restaurant9,restaurant10,restaurant11,restaurant12,restaurant13,restaurant14,restaurant15,restaurant16,restaurant17,restaurant18,restaurant19])
        restaurant1.category= cat_thucannhanh
        restaurant2.category = cat_comtam
        restaurant3.category = cat_thucannhanh
        restaurant4.category = cat_thucannhanh
        restaurant5.category = cat_thucannhanh
        restaurant6.category = cat_thucannhanh
        restaurant7.category = cat_amthucviet
        restaurant8.category = cat_monnhat
        restaurant9.category = cat_amthucviet
        restaurant10.category = cat_monnhat
        restaurant11.category = cat_thucannhanh
        restaurant12.category = cat_cafe
        restaurant13.category = cat_amthucviet
        restaurant14.category = cat_thucannhanh
        restaurant15.category = cat_amthucviet
        restaurant16.category = cat_amthucviet
        restaurant17.category = cat_cafe
        restaurant18.category = cat_monnhat
        restaurant19.category = cat_amthucviet
        db.session.commit()

        #=====================================================================================================================
        # 10. Tạo DishGroup cho nhà hàng đó
        group_com_chinh = DishGroup(name='Món Cơm Chính', restaurant_id=restaurant1.id)
        group_canh = DishGroup(name='Các Món Canh', restaurant_id=restaurant1.id)
        db.session.add_all([group_com_chinh, group_canh])
        db.session.commit()

        #=====================================================================================================================
        # 4. TẠO MÓN ĂN CHO NHÀ HÀNG
        dish1_1 = Dish(restaurant_id=restaurant1.id,
                       name='Cơm tấm sườn',
                       price=35000,
                       description='Một miếng sườn cốt lết nướng thơm lừng trên than hồng, ăn kèm với cơm tấm nóng hổi, mỡ hành và nước mắm chua ngọt.')
        dish1_2 = Dish(restaurant_id=restaurant1.id,
                       name='Cơm tấm bì chả',
                       price=30000,
                       description='Sự kết hợp hoàn hảo giữa bì heo thái sợi giòn dai và chả trứng hấp mềm mịn, béo ngậy.')

        dish1_3 = Dish(restaurant_id=restaurant1.id,
                       name='Canh khổ qua',
                       price=10000,
                       description='Canh khổ qua dồn thịt thanh mát, giải nhiệt, vị đắng nhẹ đặc trưng, tốt cho sức khỏe.')

        dish2_1 = Dish(restaurant_id=restaurant2.id, name='Bún bò đặc biệt', price=55000)
        dish2_2 = Dish(restaurant_id=restaurant2.id, name='Bún bò giò nạm', price=45000)

        db.session.add_all([dish1_1, dish1_2, dish1_3, dish2_1, dish2_2])
        dish1_1.group= group_com_chinh
        dish1_2.group= group_com_chinh
        dish1_3.group = group_canh
        dish2_1.group = group_com_chinh
        dish2_2.group = group_com_chinh
        db.session.commit()

        #=====================================================================================================================
        # 5. TẠO OPTION GROUP --> GÁN CHO MÓN ĂN CÓ GROUP OPTION --> TẠO CÁC OPTION CON CỦA OPTION GROUP
        og1 = DishOptionGroup(restaurant_id=restaurant1.id, name='Đường', mandatory=True, max=1)
        og2 = DishOptionGroup(restaurant_id=restaurant1.id, name='Đá', mandatory=True, max=1)
        og3 = DishOptionGroup(restaurant_id=restaurant1.id, name='Toping', mandatory=True, max=5)
        db.session.add_all([og1, og2, og3])
        db.session.commit()

        #Gán món ăn có DishOptionGroup
        dish1_1.option_groups.append(og1)
        dish1_1.option_groups.append(og2)
        dish1_1.option_groups.append(og3)

        #Tạo DishOption
        dish_op1 = DishOption(option_group_id=og1.id, name='50% đường', price=0)
        dish_op2 = DishOption(option_group_id=og1.id, name='70% đường', price=0)
        dish_op3 = DishOption(option_group_id=og1.id, name='100% đường', price=0)

        dish_op4 = DishOption(option_group_id=og2.id, name='50% đá', price=0)
        dish_op5 = DishOption(option_group_id=og2.id, name='100% đá', price=0)
        dish_op6 = DishOption(option_group_id=og2.id, name='Đá riêng', price=0)

        dish_op7 = DishOption(option_group_id=og3.id, name='Trân châu trắng', price=5000)
        dish_op8 = DishOption(option_group_id=og3.id, name='Trân châu đen', price=5000)
        dish_op9 = DishOption(option_group_id=og3.id, name='Thạch dừa', price=5000)

        db.session.add_all([dish_op1, dish_op2, dish_op3, dish_op4, dish_op5, dish_op6, dish_op7, dish_op8, dish_op9])
        db.session.commit()

        #=====================================================================================================================
        # 6. TẠO VOUCHER
        voucher1 = Voucher(code='GIAM10K', name='Giảm 10k cho đơn từ 50k', percent=0, limit=10000, min=50000, max=10000,
                           start_date=datetime.datetime.now(),
                           end_date=datetime.datetime.now() + datetime.timedelta(days=30))
        voucher2 = Voucher(code='FREESHIP', name='Miễn phí vận chuyển', percent=0, limit=15000, min=30000, max=15000,
                           start_date=datetime.datetime.now(),
                           end_date=datetime.datetime.now() + datetime.timedelta(days=30))
        db.session.add_all([voucher1, voucher2])
        db.session.commit()

        #=====================================================================================================================
        # 7. TẠO ĐƠN HÀNG VÀ CHI TIẾT ĐƠN HÀNG
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

        # Đơn hàng 3 của customer2 tại restaurant2
        order3_subtotal = dish2_1.price * 2  # 2 tô bún bò đặc biệt
        order3_total = order3_subtotal  # Không có giảm giá
        order3 = Order(user_id=customer2.id, restaurant_id=restaurant2.id, subtotal=order3_subtotal,
                       total=order3_total, delivery_address='100 Nguyễn Trãi, Quận 5, TP.HCM',
                       order_status=OrderState.DELIVERING)
        db.session.add(order3)
        db.session.commit()

        detail3_1 = OrderDetail(order_id=order3.id, dish_id=dish2_1.id, quantity=2, price=dish2_1.price,
                                dish_name=dish2_1.name, selected_options_luc_dat={})
        db.session.add(detail3_1)
        db.session.commit()

        # 6. TẠO ĐÁNH GIÁ (REVIEW)
        # Chỉ những đơn hàng đã COMPLETED mới có thể có review.css
        review1 = Review(user_id=order1.user_id, restaurant_id=order1.restaurant_id, order_id=order1.id,
                         star=5, comment='Cơm tấm ngon, giao hàng nhanh. Sẽ ủng hộ tiếp!')
        db.session.add(review1)
        db.session.commit()




        # 4. Tạo Món ăn và gán vào DishGroup
        com_tam = Dish(name='Cơm tấm đặc biệt', price=35000, restaurant_id=restaurant1.id, group=group_com_chinh)
        canh_kho_qua = Dish(name='Canh khổ qua', price=10000, restaurant_id=restaurant1.id, group=group_canh)
        db.session.add_all([com_tam, canh_kho_qua])
        db.session.commit()

        print("\n--- Bắt đầu thêm DishGroup, Dish, và Options chi tiết ---")

        # --- Dữ liệu cho Jollibee (restaurant3) ---
        print("Tạo dữ liệu cho Jollibee (restaurant3)...")
        group_j_ga = DishGroup(name='Gà Giòn Vui Vẻ', restaurant_id=restaurant3.id)
        group_j_monphu = DishGroup(name='Mì Ý & Cơm', restaurant_id=restaurant3.id)
        group_j_trangmieng = DishGroup(name='Tráng Miệng & Thức Uống', restaurant_id=restaurant3.id)
        db.session.add_all([group_j_ga, group_j_monphu, group_j_trangmieng])
        db.session.commit()

        dish_j_1 = Dish(restaurant_id=restaurant3.id, group=group_j_ga, name='1 Miếng Gà Rán', price=36000,description='Một miếng gà giòn rụm, tẩm ướp theo công thức độc quyền, có thể chọn vị cay hoặc không cay.')
        dish_j_2 = Dish(restaurant_id=restaurant3.id, group=group_j_ga, name='Combo 2 Miếng Gà Rán', price=85000,description='Combo tiết kiệm gồm 2 miếng gà giòn tan, khoai tây và nước ngọt. Lựa chọn hoàn hảo cho bữa ăn no nê.')
        dish_j_3 = Dish(restaurant_id=restaurant3.id, group=group_j_monphu, name='Mì Ý Sốt Bò Bằm', price=35000,description='Sợi mì Ý dai ngon hòa quyện cùng sốt bò bằm đậm đà, rắc thêm phô mai béo ngậy.')
        dish_j_4 = Dish(restaurant_id=restaurant3.id, group=group_j_trangmieng, name='Bánh Xoài Đào', price=25000, description='Bánh nướng giòn tan với nhân xoài và đào chua ngọt, món tráng miệng tuyệt vời.')
        dish_j_5 = Dish(restaurant_id=restaurant3.id, group=group_j_trangmieng, name='Pepsi Lon', price=15000, active=False,description='Nước ngọt Pepsi mát lạnh, giải khát tức thì.')
        db.session.add_all([dish_j_1, dish_j_2, dish_j_3, dish_j_4, dish_j_5])
        db.session.commit()

        # Tùy chọn cho món "1 Miếng Gà Rán"
        opt_group_j_1 = DishOptionGroup(restaurant_id=restaurant3.id, name='Chọn Phần Gà', mandatory=True, max=1)
        db.session.add(opt_group_j_1)
        db.session.commit()
        dish_j_1.option_groups.append(opt_group_j_1)
        db.session.commit()
        opt_j_1_1 = DishOption(option_group_id=opt_group_j_1.id, name='Má Đùi (Cay)', price=0)
        opt_j_1_2 = DishOption(option_group_id=opt_group_j_1.id, name='Má Đùi (Không Cay)', price=0)
        opt_j_1_3 = DishOption(option_group_id=opt_group_j_1.id, name='Cánh (Cay)', price=0)
        db.session.add_all([opt_j_1_1, opt_j_1_2, opt_j_1_3])
        db.session.commit()

        # Tùy chọn cho "Combo 2 Miếng Gà Rán"
        opt_group_j_2 = DishOptionGroup(restaurant_id=restaurant3.id, name='Chọn 2 Phần Gà', mandatory=True, max=2)
        opt_group_j_3 = DishOptionGroup(restaurant_id=restaurant3.id, name='Đổi Nước Lớn', mandatory=False, max=1)
        db.session.add_all([opt_group_j_2, opt_group_j_3])
        db.session.commit()
        dish_j_2.option_groups.append(opt_group_j_2)
        dish_j_2.option_groups.append(opt_group_j_3)
        db.session.commit()

        opt_j_2_1 = DishOption(option_group_id=opt_group_j_2.id, name='Má Đùi (Cay)', price=0)
        opt_j_2_2 = DishOption(option_group_id=opt_group_j_2.id, name='Má Đùi (Không Cay)', price=0)
        opt_j_2_3 = DishOption(option_group_id=opt_group_j_2.id, name='Cánh (Cay)', price=0)
        opt_j_3_1 = DishOption(option_group_id=opt_group_j_3.id, name='Đổi Pepsi Lớn (+5k)', price=5000)
        db.session.add_all([opt_j_2_1, opt_j_2_2, opt_j_2_3, opt_j_3_1])
        db.session.commit()

        # --- Dữ liệu cho Bánh Mì Huỳnh Gia (restaurant4) ---
        print("Tạo dữ liệu cho Bánh Mì Huỳnh Gia (restaurant4)...")
        group_bm_chinh = DishGroup(name='Bánh Mì Đặc Trưng', restaurant_id=restaurant4.id)
        group_bm_phu = DishGroup(name='Món Thêm', restaurant_id=restaurant4.id)
        db.session.add_all([group_bm_chinh, group_bm_phu])
        db.session.commit()

        dish_bm_1 = Dish(restaurant_id=restaurant4.id, group=group_bm_chinh, name='Bánh Mì Heo Quay Đặc Biệt',
                         price=45000)
        dish_bm_2 = Dish(restaurant_id=restaurant4.id, group=group_bm_chinh, name='Bánh Mì Thịt Nướng', price=35000)
        dish_bm_3 = Dish(restaurant_id=restaurant4.id, group=group_bm_phu, name='Xôi Heo Quay', price=30000)
        db.session.add_all([dish_bm_1, dish_bm_2, dish_bm_3])
        db.session.commit()

        # Tùy chọn cho Bánh Mì
        opt_group_bm_1 = DishOptionGroup(restaurant_id=restaurant4.id, name='Yêu cầu thêm', mandatory=False, max=2)
        db.session.add(opt_group_bm_1)
        db.session.commit()
        dish_bm_1.option_groups.append(opt_group_bm_1)
        db.session.commit()
        opt_bm_1_1 = DishOption(option_group_id=opt_group_bm_1.id, name='Thêm Pate', price=7000)
        opt_bm_1_2 = DishOption(option_group_id=opt_group_bm_1.id, name='Thêm Trứng Ốp La', price=8000)
        opt_bm_1_3 = DishOption(option_group_id=opt_group_bm_1.id, name='Không lấy rau', price=0)
        db.session.add_all([opt_bm_1_1, opt_bm_1_2, opt_bm_1_3])
        db.session.commit()

        # --- Dữ liệu cho Phở Lệ (restaurant7) ---
        print("Tạo dữ liệu cho Phở Lệ (restaurant7)...")
        group_pho_chinh = DishGroup(name='Phở Bò', restaurant_id=restaurant7.id)
        group_pho_them = DishGroup(name='Món Ăn Kèm', restaurant_id=restaurant7.id)
        db.session.add_all([group_pho_chinh, group_pho_them])
        db.session.commit()

        dish_pho_1 = Dish(restaurant_id=restaurant7.id, group=group_pho_chinh, name='Phở Tái', price=65000)
        dish_pho_2 = Dish(restaurant_id=restaurant7.id, group=group_pho_chinh, name='Phở Nạm Gầu', price=75000)
        dish_pho_3 = Dish(restaurant_id=restaurant7.id, group=group_pho_them, name='Chén Trứng Trần', price=7000)
        dish_pho_4 = Dish(restaurant_id=restaurant7.id, group=group_pho_them, name='Giò Cháo Quẩy', price=5000)
        db.session.add_all([dish_pho_1, dish_pho_2, dish_pho_3, dish_pho_4])
        db.session.commit()

        opt_group_pho_1 = DishOptionGroup(restaurant_id=restaurant7.id, name='Yêu cầu', mandatory=False, max=1)
        db.session.add(opt_group_pho_1)
        db.session.commit()
        dish_pho_1.option_groups.append(opt_group_pho_1)
        db.session.commit()
        opt_pho_1_1 = DishOption(option_group_id=opt_group_pho_1.id, name='Nhiều bánh phở', price=0)
        opt_pho_1_2 = DishOption(option_group_id=opt_group_pho_1.id, name='Không hành', price=0)
        db.session.add_all([opt_pho_1_1, opt_pho_1_2])
        db.session.commit()

        # --- Dữ liệu cho Gogi House (restaurant8) ---
        print("Tạo dữ liệu cho Gogi House (restaurant8)...")
        group_gogi_combo = DishGroup(name='Combo Nướng', restaurant_id=restaurant8.id)
        group_gogi_lau = DishGroup(name='Lẩu Hàn Quốc', restaurant_id=restaurant8.id)
        db.session.add_all([group_gogi_combo, group_gogi_lau])
        db.session.commit()

        dish_gogi_1 = Dish(restaurant_id=restaurant8.id, group=group_gogi_combo, name='Combo Thịt Nướng 2 Người',
                           price=399000)
        dish_gogi_2 = Dish(restaurant_id=restaurant8.id, group=group_gogi_lau, name='Lẩu Kim Chi Hải Sản', price=259000)
        db.session.add_all([dish_gogi_1, dish_gogi_2])
        db.session.commit()

        opt_group_gogi_1 = DishOptionGroup(restaurant_id=restaurant8.id, name='Chọn Độ Cay', mandatory=True, max=1)
        opt_group_gogi_2 = DishOptionGroup(restaurant_id=restaurant8.id, name='Thêm Món Nhúng', mandatory=False, max=3)
        db.session.add_all([opt_group_gogi_1, opt_group_gogi_2])
        db.session.commit()
        dish_gogi_2.option_groups.append(opt_group_gogi_1)
        dish_gogi_2.option_groups.append(opt_group_gogi_2)
        db.session.commit()
        opt_gogi_1_1 = DishOption(option_group_id=opt_group_gogi_1.id, name='Ít Cay', price=0)
        opt_gogi_1_2 = DishOption(option_group_id=opt_group_gogi_1.id, name='Cay Vừa', price=0)
        opt_gogi_2_1 = DishOption(option_group_id=opt_group_gogi_2.id, name='Thêm Ba Chỉ Bò Mỹ', price=89000)
        opt_gogi_2_2 = DishOption(option_group_id=opt_group_gogi_2.id, name='Thêm Nấm Kim Châm', price=30000)
        opt_gogi_2_3 = DishOption(option_group_id=opt_group_gogi_2.id, name='Thêm Mực Ống', price=79000)
        db.session.add_all([opt_gogi_1_1, opt_gogi_1_2, opt_gogi_2_1, opt_gogi_2_2, opt_gogi_2_3])
        db.session.commit()

        # --- Dữ liệu cho The Coffee House (restaurant12) ---
        print("Tạo dữ liệu cho The Coffee House (restaurant12)...")
        group_tch_cafe = DishGroup(name='Cà Phê', restaurant_id=restaurant12.id)
        group_tch_tra = DishGroup(name='Trà & Macchiato', restaurant_id=restaurant12.id)
        group_tch_banh = DishGroup(name='Bánh Ngọt', restaurant_id=restaurant12.id)
        db.session.add_all([group_tch_cafe, group_tch_tra, group_tch_banh])
        db.session.commit()

        dish_tch_1 = Dish(restaurant_id=restaurant12.id, group=group_tch_cafe, name='Cà Phê Sữa Đá', price=35000)
        dish_tch_2 = Dish(restaurant_id=restaurant12.id, group=group_tch_tra, name='Trà Đào Cam Sả', price=55000)
        dish_tch_3 = Dish(restaurant_id=restaurant12.id, group=group_tch_banh, name='Bánh Tiramisu', price=35000)
        db.session.add_all([dish_tch_1, dish_tch_2, dish_tch_3])
        db.session.commit()

        opt_group_tch_1 = DishOptionGroup(restaurant_id=restaurant12.id, name='Chọn Size', mandatory=True, max=1)
        opt_group_tch_2 = DishOptionGroup(restaurant_id=restaurant12.id, name='Mức Đường', mandatory=False, max=1)
        db.session.add_all([opt_group_tch_1, opt_group_tch_2])
        db.session.commit()
        dish_tch_2.option_groups.append(opt_group_tch_1)
        dish_tch_2.option_groups.append(opt_group_tch_2)
        db.session.commit()
        opt_tch_1_1 = DishOption(option_group_id=opt_group_tch_1.id, name='Size M', price=0)
        opt_tch_1_2 = DishOption(option_group_id=opt_group_tch_1.id, name='Size L', price=10000)
        opt_tch_2_1 = DishOption(option_group_id=opt_group_tch_2.id, name='100% Đường', price=0)
        opt_tch_2_2 = DishOption(option_group_id=opt_group_tch_2.id, name='70% Đường', price=0)
        opt_tch_2_3 = DishOption(option_group_id=opt_group_tch_2.id, name='50% Đường', price=0)
        db.session.add_all([opt_tch_1_1, opt_tch_1_2, opt_tch_2_1, opt_tch_2_2, opt_tch_2_3])
        db.session.commit()

        # --- Dữ liệu cho các nhà hàng còn lại (dạng đơn giản hơn) ---
        print("Tạo dữ liệu đơn giản cho các nhà hàng còn lại...")
        # Lẩu Dê 404 (restaurant9)
        group_ld_lau = DishGroup(name='Lẩu & Nướng', restaurant_id=restaurant9.id)
        db.session.add(group_ld_lau)
        db.session.commit()
        db.session.add_all([
            Dish(restaurant_id=restaurant9.id, group=group_ld_lau, name='Lẩu Dê Nhỏ', price=200000),
            Dish(restaurant_id=restaurant9.id, group=group_ld_lau, name='Dê Nướng', price=150000)
        ])

        # Sushi Hokkaido (restaurant10)
        group_sushi_chinh = DishGroup(name='Sushi & Sashimi', restaurant_id=restaurant10.id)
        db.session.add(group_sushi_chinh)
        db.session.commit()
        db.session.add_all([
            Dish(restaurant_id=restaurant10.id, group=group_sushi_chinh, name='Sashimi Cá Hồi (3 miếng)', price=120000),
            Dish(restaurant_id=restaurant10.id, group=group_sushi_chinh, name='Salad Da Cá Hồi', price=85000)
        ])

        # KFC (restaurant11)
        group_kfc_combo = DishGroup(name='Combo & Burger', restaurant_id=restaurant11.id)
        db.session.add(group_kfc_combo)
        db.session.commit()
        db.session.add_all([
            Dish(restaurant_id=restaurant11.id, group=group_kfc_combo, name='Combo Gà Rán A', price=89000),
            Dish(restaurant_id=restaurant11.id, group=group_kfc_combo, name='Burger Tôm', price=45000)
        ])

        # Pizza Hut (restaurant14)
        group_pizza_chinh = DishGroup(name='Pizza & Mì Ý', restaurant_id=restaurant14.id)
        db.session.add(group_pizza_chinh)
        db.session.commit()
        db.session.add_all([
            Dish(restaurant_id=restaurant14.id, group=group_pizza_chinh, name='Pizza Hải Sản Pesto Xanh', price=159000),
            Dish(restaurant_id=restaurant14.id, group=group_pizza_chinh, name='Mì Ý Hải Sản', price=99000)
        ])

        # Lẩu Nấm Ashima (restaurant15)
        group_ln_chinh = DishGroup(name='Món Đặc Trưng', restaurant_id=restaurant15.id)
        db.session.add(group_ln_chinh)
        db.session.commit()
        db.session.add_all([
            Dish(restaurant_id=restaurant15.id, group=group_ln_chinh, name='Canh Nấm Bổ Dưỡng', price=120000),
            Dish(restaurant_id=restaurant15.id, group=group_ln_chinh, name='Gà Hầm Nấm', price=250000)
        ])

        # Bò Tơ Củ Chi (restaurant16)
        group_bt_chinh = DishGroup(name='Đặc Sản Bò Tơ', restaurant_id=restaurant16.id)
        db.session.add(group_bt_chinh)
        db.session.commit()
        db.session.add_all([
            Dish(restaurant_id=restaurant16.id, group=group_bt_chinh, name='Bò Tơ Nướng Tảng', price=300000),
            Dish(restaurant_id=restaurant16.id, group=group_bt_chinh, name='Lòng Bò Luộc', price=150000)
        ])

        # Highlands (restaurant17)
        group_hl_cafe = DishGroup(name='Cà Phê & Trà', restaurant_id=restaurant17.id)
        db.session.add(group_hl_cafe)
        db.session.commit()
        db.session.add_all([
            Dish(restaurant_id=restaurant17.id, group=group_hl_cafe, name='Phin Sữa Đá', price=35000),
            Dish(restaurant_id=restaurant17.id, group=group_hl_cafe, name='Trà Sen Vàng', price=45000)
        ])

        # Marukame Udon (restaurant18)
        group_mu_chinh = DishGroup(name='Mì Udon & Tempura', restaurant_id=restaurant18.id)
        db.session.add(group_mu_chinh)
        db.session.commit()
        db.session.add_all([
            Dish(restaurant_id=restaurant18.id, group=group_mu_chinh, name='Udon Bò', price=89000),
            Dish(restaurant_id=restaurant18.id, group=group_mu_chinh, name='Tempura Rau Củ', price=25000)
        ])

        # Bánh Xèo Ăn Là Ghiền (restaurant19)
        group_bx_chinh = DishGroup(name='Bánh Xèo & Gỏi Cuốn', restaurant_id=restaurant19.id)
        db.session.add(group_bx_chinh)
        db.session.commit()
        db.session.add_all([
            Dish(restaurant_id=restaurant19.id, group=group_bx_chinh, name='Bánh Xèo Tôm Thịt', price=50000),
            Dish(restaurant_id=restaurant19.id, group=group_bx_chinh, name='Gỏi Cuốn', price=30000)
        ])

        db.session.commit()


        print("--- TẠO DỮ LIỆU THỬ NGHIỆM THÀNH CÔNG ---")

