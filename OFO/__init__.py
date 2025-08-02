from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from urllib.parse import quote  # Do mật khẩu DB có ký tự đặc biệt
import cloudinary
from flask_socketio import SocketIO

app = Flask(__name__)

app.secret_key = 'SDASDEW!21321321s2'

app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:%s@localhost/ofodb?charset=utf8mb4" % quote('admin')
# TB1: Driver CSDL kết nối ;; TB2: Un,pass CSDL mình kết nối ;; TB3: Server chạy DB ;; TB4: Tên DB ;; TB5: Cờ tương tác tiếng việt dễ dàng
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config["SO_PHAN_TU"] = 10  # Thông số cấu hình số sản phẩm 1 trang (8)
app.config.from_pyfile('config.py')
db = SQLAlchemy(app)
login = LoginManager(app)
socketio = SocketIO(app)


cloudinary.config(  # Paste cấu hình vào
    cloud_name="dq2jtbrda",
    api_key="341769211452564",
    api_secret="_5G4itRP_2YE52K8srR6cJO5Las",
    secure=True
)