# run.py

# 1. Import hàm create_app và đối tượng socketio từ __init__
from __init__ import create_app, socketio

# 2. Tạo một phiên bản ứng dụng
app = create_app('development')

# 3. Chạy ứng dụng bằng socketio.run()
if __name__ == '__main__':
    # Dùng host='0.0.0.0' nếu bạn muốn truy cập từ máy khác trong mạng
    # Hoặc dùng host='127.0.0.1' để chỉ truy cập từ máy của bạn
    socketio.run(app, host='127.0.0.1', port=5000, debug=True)