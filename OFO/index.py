from flask import Flask, render_template, request, redirect, url_for, flash
from __init__ import app, db, login
import dao
from flask_login import login_user,logout_user
from models import *
from flask import request, jsonify
from flask import session


@app.route("/")
def index():
    return render_template('index.html')

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

        dao.add_user(**data)
        return redirect('/login')

    return render_template('register.html', phone=phone)



#Restaurant
@app.route('/resregister')
def resregister():
    return render_template('Restaurant/ResRegister.html')
  
@app.route('/reslogin')
def reslogin():
    return render_template('Restaurant/ResLogin.html')

@app.route("/tim-kiem")
def tim_kiem():
    return render_template('tim-kiem.html')

@login.user_loader
def get_user_by_id(user_id):
    return dao.get_user_by_id(user_id)
import admin
if __name__ == '__main__':
    with app.app_context():
        app.run(debug=True)
