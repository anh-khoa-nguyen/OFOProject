#!/bin/bash

# Dòng này đảm bảo script sẽ dừng lại ngay lập tức nếu có bất kỳ lệnh nào bị lỗi
set -e

# Chạy lệnh khởi tạo cơ sở dữ liệu
echo "---- [startup.sh] Bắt đầu chạy create_db.py ----"
python create_db.py
echo "---- [startup.sh] create_db.py đã chạy xong ----"

# Sau khi khởi tạo xong, chạy lệnh Gunicorn để khởi động web server
# Lệnh 'exec' sẽ thay thế tiến trình của script này bằng tiến trình gunicorn
# Đây là cách làm đúng để gunicorn trở thành tiến trình chính (PID 1) của container
echo "---- [startup.sh] Bắt đầu khởi động Gunicorn server ----"
exec gunicorn --bind 0.0.0.0:5000 --workers 1 manage:app