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
    lat = Column(Numeric(10, 7), nullable=True)
    lng = Column(Numeric(10, 7), nullable=True)
    description = Column(String(100))
    image = Column(String(100),
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
    carts = relationship('Cart', backref='restaurant', lazy=True)


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
    options = relationship('DishOption', backref='dish_option_group', lazy=True)

class DishOption(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    option_group_id = Column(Integer, ForeignKey(DishOptionGroup.id), nullable=False)
    name = Column(String(50), nullable=False)
    price = Column(Float, default=0)



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
        db.drop_all()
        db.create_all()
        db.session.commit()

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

        db.session.add_all([admin_user, owner1, owner2, customer1, customer2])
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

        db.session.add_all(
            [cat_hutieu, cat_trasua, cat_thucannhanh, cat_comtam, cat_banhmi, cat_chao, cat_thitga, cat_pizza])
        db.session.commit()

        #=====================================================================================================================
        # 2. TẠO NHÀ HÀNG (PROFILE)
        restaurant1 = Restaurant(owner_user_id=owner1.id,
                                 restaurant_name='Mì Trộn Tên Lửa - CMT8',
                                 address='111 Cách Mạng Tháng Tám, P. 1, Q. 3, TP.HCM',
                                 description='Mì trộn độc đáo với các loại sốt nhà làm.',
                                 image='https://res.cloudinary.com/dq2jtbrda/image/upload/v1752910914/mitron_bbzzqc.jpg',
                                 category=cat_thucannhanh,
                                 # Thêm giờ mở/đóng cửa
                                 open_time=time(10, 0),  # 10:00 AM
                                 close_time=time(22, 0),
                                 active=True)  # 10:00 PM,

        restaurant2 = Restaurant(owner_user_id=owner2.id,
                                 restaurant_name='Tiệm Cơm Nhà Trộn - Phú Nhuận',
                                 address='222 Phan Xích Long, P. 2, Q. Phú Nhuận, TP.HCM',
                                 description='Cơm trộn Hàn Quốc chuẩn vị cho giới trẻ.',
                                 image='https://res.cloudinary.com/dq2jtbrda/image/upload/v1752910914/comtron_qhxxer.jpg',
                                 category=cat_comtam,
                                 # Thêm giờ mở/đóng cửa
                                 open_time=time(11, 0),  # 11:00 AM
                                 close_time=time(21, 30),
                                 active=True)  # 09:30 PM

        restaurant3 = Restaurant(owner_user_id=owner2.id,
                                 restaurant_name='Jollibee - EC Tô Hiến Thành',
                                 address='333 Tô Hiến Thành, P. 13, Q. 10, TP.HCM',
                                 description='Gà giòn vui vẻ, Mì Ý sốt bò bằm.',
                                 image='https://res.cloudinary.com/dq2jtbrda/image/upload/v1752910914/garan_mzz4tb.webp',
                                 category=cat_thitga,
                                 # Thêm giờ mở/đóng cửa
                                 open_time=time(9, 0),  # 09:00 AM
                                 close_time=time(22, 45),
                                 active=True)  # 10:45 PM

        restaurant4 = Restaurant(owner_user_id=owner1.id,
                                 restaurant_name='Bánh Mì Huỳnh Gia - Lê Văn Lương',
                                 address='444 Lê Văn Lương, P. Tân Hưng, Q. 7, TP.HCM',
                                 description='Bánh mì heo quay da giòn trứ danh.',
                                 image='https://res.cloudinary.com/dq2jtbrda/image/upload/v1752910913/banhmi_w70ph8.webp',
                                 category=cat_banhmi,
                                 # Thêm giờ mở/đóng cửa
                                 open_time=time(6, 30),  # 06:30 AM
                                 close_time=time(20, 0),
                                 active=True)  # 08:00 PM

        #=====================================================================================================================
        # 3. KHÁCH YÊU THÍCH NHÀ HÀNG
        customer1.favorite_restaurants.append(restaurant1)
        customer1.favorite_restaurants.append(restaurant2)
        customer2.favorite_restaurants.append(restaurant3)

        db.session.add_all([restaurant1, restaurant2, restaurant3, restaurant4])
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
                       description='Một miếng sườn cốt lết nướng thơm lừng trên than hồng, ăn kèm với cơm tấm nóng hổi, mỡ hành và nước mắm chua ngọt.',
                       group=group_com_chinh)
        dish1_2 = Dish(restaurant_id=restaurant1.id,
                       name='Cơm tấm bì chả',
                       price=30000,
                       description='Sự kết hợp hoàn hảo giữa bì heo thái sợi giòn dai và chả trứng hấp mềm mịn, béo ngậy.',
                       group=group_com_chinh)

        dish1_3 = Dish(restaurant_id=restaurant1.id,
                       name='Canh khổ qua',
                       price=10000,
                       description='Canh khổ qua dồn thịt thanh mát, giải nhiệt, vị đắng nhẹ đặc trưng, tốt cho sức khỏe.',
                       group=group_canh)

        dish2_1 = Dish(restaurant_id=restaurant2.id, name='Bún bò đặc biệt', price=55000)
        dish2_2 = Dish(restaurant_id=restaurant2.id, name='Bún bò giò nạm', price=45000)

        db.session.add_all([dish1_1, dish1_2, dish1_3, dish2_1, dish2_2])
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

        #=====================================================================================================================
        # 8. TẠO ĐÁNH GIÁ (REVIEW)
        # Chỉ những đơn hàng đã COMPLETED mới có thể có review
        review1 = Review(user_id=order1.user_id, restaurant_id=order1.restaurant_id, order_id=order1.id,
                         star=5, comment='Cơm tấm ngon, giao hàng nhanh. Sẽ ủng hộ tiếp!')
        db.session.add(review1)
        db.session.commit()


        print("--- TẠO DỮ LIỆU THỬ NGHIỆM THÀNH CÔNG ---")

