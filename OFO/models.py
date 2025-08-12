import datetime
from datetime import time
from sqlalchemy import (Column, Integer, String, Boolean, Float, ForeignKey,
                        Enum, DateTime, Time, JSON, Numeric)
from sqlalchemy.orm import relationship
from flask_login import UserMixin
from enum import Enum as PyEnum
from __init__ import db


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

    restaurants_owned = relationship('Restaurant', back_populates='user', lazy=True)
    orders = relationship('Order', backref='user', lazy=True)
    reviews = relationship('Review', backref='user', lazy=True)
    # carts = relationship('Cart', backref='user', lazy=True)
    def __str__(self):
        return self.name


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
    user = relationship('User', back_populates='restaurants_owned')
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
    UNPAID = 'Chưa thanh toán'
    PENDING = "Pending"
    CONFIRMED = "Confirmed"
    DELIVERING = "Delivering"
    COMPLETED = "Completed"

class Order(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False, index=True)
    restaurant_id = Column(Integer, ForeignKey(Restaurant.id), nullable=False, index=True)
    order_date = Column(DateTime, default=datetime.datetime.now)
    shipping_fee = Column(Float, default=0)
    subtotal = Column(Float, nullable=False)  # tổng tiền
    discount = Column(Float, default=0)
    total = Column(Float, nullable=False)  # thành tiền
    delivery_address = Column(String(255), nullable=False)
    note = Column(String(100))
    order_status = Column(Enum(OrderState), default=OrderState.PENDING, nullable=False)
    estimated_delivery_time = Column(DateTime, nullable=True)
    delivery_time = Column(Integer, nullable=True)

    details = relationship('OrderDetail', backref='order', lazy=True)
    review = relationship('Review', backref='order', uselist=False, cascade="all, delete-orphan")
    payments = relationship('Payment', back_populates='order', lazy=True, cascade="all, delete-orphan")

class PaymentStatus(PyEnum):
    UNPAID = "Chưa thanh toán"
    PAID = "Đã thanh toán"
    FAILED = "Thất bại"

class Payment(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey('order.id'), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    payment_method = Column(String(20), nullable=False)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.UNPAID, nullable=False)
    created_date = Column(DateTime, default=datetime.datetime.now)

    # Các trường dành riêng cho MoMo
    pay_url = Column(String(500), nullable=True)
    momo_order_id = Column(String(255), nullable=True, unique=True)
    order = relationship('Order', back_populates='payments')


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
    restaurant_id = Column(Integer, ForeignKey(Restaurant.id), nullable=False, index=True)


voucher_applied = db.Table('voucher_applied',
                           Column('order_id', Integer, ForeignKey('order.id'), primary_key=True),
                           Column('voucher_id', Integer, ForeignKey('voucher.id'), primary_key=True)
                           )

Order.vouchers = relationship('Voucher', secondary=voucher_applied, lazy='subquery',
                              backref=db.backref('orders_applied', lazy=True))
restaurant = relationship('Restaurant', backref='vouchers')

