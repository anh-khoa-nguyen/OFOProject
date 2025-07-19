import datetime
from sqlalchemy import (Column, Integer, String, Boolean, Float, ForeignKey,
                        Enum, DateTime, Time, JSON)
from sqlalchemy.orm import relationship
from flask_login import UserMixin
from enum import Enum as PyEnum
from . import db, app

class UserRole(PyEnum):
    USER = 'user'
    RESTAURANT = 'restaurant'
    ADMIN = 'admin'

class User(db.Model, UserMixin):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    email = Column(String(50), nullable=False, unique=True)
    phone = Column(String(10), unique=True, index=True)
    password = Column(String(50), nullable=False)
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

class Restaurant(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    owner_user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    restaurant_name = Column(String(50), nullable=False)
    address = Column(String(100))
    email = Column(String(50), unique=True)
    description = Column(String(100))
    image = Column(String(100), default='https://res.cloudinary.com/dxxwcby8l/image/upload/v1647056401/ipmsmnxjydrhpo21xrd8.jpg')
    open_time = Column(Time)
    close_time = Column(Time)
    status = Column(Boolean, default=True)
    active = Column(Boolean, default=False)

    created_date = Column(DateTime, default=datetime.datetime.now)

    # Relationships
    favorited_by_users = relationship('User', secondary=favorite_restaurants, lazy='subquery',
                                      backref=db.backref('favorite_restaurants', lazy=True))

    dishes = relationship('Dish', backref='restaurant', lazy=True)
    orders = relationship('Order', backref='restaurant', lazy=True)
    reviews = relationship('Review', backref='restaurant', lazy=True)
    carts = relationship('Cart', backref='restaurant', lazy=True)

class Dish(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    restaurant_id = Column(Integer, ForeignKey(Restaurant.id), nullable=False, index=True)
    name = Column(String(50), nullable=False)
    description = Column(String(100))
    price = Column(Float, nullable=False, default=0)
    image = Column(String(100))

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
    subtotal = Column(Float, nullable=False) #tổng tiền
    discount = Column(Float, default=0) #giảm giá
    total = Column(Float, nullable=False) #thành tiền
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
    order = relationship('Order', backref=db.backref('review', uselist=False), lazy=True)

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