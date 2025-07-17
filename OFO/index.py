from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)

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

@app.route("/tim-kiem")
def tim_kiem():
    return render_template('tim-kiem.html')

if __name__ == '__main__':
    with app.app_context():
        app.run(debug=True)
