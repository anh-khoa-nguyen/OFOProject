import json
import os
import config
import hashlib
from  models import *
from __init__ import db,app

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

 db.session.add(u)
 db.session.commit()

if __name__ == "__main__":
    print(auth_user("user", 123))