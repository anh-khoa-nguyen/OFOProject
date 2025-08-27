import subprocess
import os
import sys

try:
    # --- PHẦN TỰ ĐỘNG XÁC ĐỊNH ĐƯỜNG DẪN ---

    # Lấy đường dẫn tuyệt đối đến file script này (ví dụ: D:\QLDA\OFOProject\OFO\run_cypress.py)
    script_path = os.path.abspath(__file__)

    # Lấy thư mục chứa file script này (ví dụ: D:\QLDA\OFOProject\OFO)
    script_dir = os.path.dirname(script_path)

    # Giả định rằng thư mục 'OFO' (chứa cypress.config.js) là thư mục chứa script này
    # Hoặc là thư mục con có tên 'OFO' nếu script nằm ở thư mục gốc.
    if os.path.basename(script_dir) == 'OFOProject':
        # Nếu script nằm ở thư mục gốc (OFOProject), thì project path là thư mục con 'OFO'
        project_path = os.path.join(script_dir, 'OFO')
    else:
        # Nếu script nằm ở bất kỳ đâu khác (bao gồm cả bên trong 'OFO'),
        # chúng ta giả định thư mục chứa nó chính là project path.
        project_path = script_dir

    # Kiểm tra xem đường dẫn có hợp lệ không trước khi chạy
    if not os.path.isdir(project_path) or not os.path.exists(os.path.join(project_path, 'cypress.config.js')):
        print(f"LỖI: Không thể tìm thấy thư mục dự án Cypress hợp lệ tại: {project_path}")
        print("Vui lòng đảm bảo file 'cypress.config.js' tồn tại bên trong thư mục đó.")
        sys.exit(1)  # Thoát script với mã lỗi

    # --- PHẦN THỰC THI LỆNH ---

    print(f">>> Đang chuẩn bị mở Cypress GUI trong thư mục: {project_path}")
    print(">>> Vui lòng chờ một lát...")

    command = ['npx', 'cypress', 'open']

    # Chạy lệnh từ đường dẫn tuyệt đối đã được xác định
    subprocess.run(command, cwd=project_path, shell=True, check=True)

    print(">>> Đã đóng Cypress GUI.")

except FileNotFoundError:
    print("LỖI: Lệnh 'npx' không được tìm thấy.")
    print("Vui lòng đảm bảo bạn đã cài đặt Node.js và nó đã được thêm vào biến môi trường PATH.")
except subprocess.CalledProcessError as e:
    print(f"LỖI: Cypress đã thoát với mã lỗi: {e.returncode}")
except KeyboardInterrupt:
    print("\n>>> Đã hủy tiến trình.")