# 🎫 Hệ thống Quản lý Sự cố & Yêu cầu CNTT (IT Ticket Management System)

Một hệ thống Helpdesk nội bộ hoàn chỉnh được xây dựng trên nền tảng **Flask (Python)**. Hệ thống giúp doanh nghiệp quản lý, theo dõi và phân công xử lý các sự cố hoặc yêu cầu hỗ trợ từ người dùng một cách hiệu quả và minh bạch, với luồng quy trình (workflow) theo sát quy chuẩn nghiệp vụ thực tế.

---

## ✨ Tính năng nổi bật

- **Quản lý đa phân quyền (Multi-role Access):**
  - Giới hạn và bảo mật thông tin hiển thị dựa theo 4 vai trò: `Admin`, `Leader` (Trưởng nhóm IT), `Staff` (Kỹ thuật viên) và `User` (Người dùng phổ thông).
- **Quy trình Ticket chuyên nghiệp (Ticket Lifecycle):**
  - Cho phép người dùng tạo, theo dõi toàn bộ trạng thái xử lý (*Đang chờ, Đang xử lý, Đã giải quyết...*).
  - Tích hợp trao đổi (Chat/Comment) theo thời gian thực (polling) giữa Kỹ thuật viên và Người dùng ngay trong từng Ticket.
  - Phân loại theo Danh mục, Độ ưu tiên, và đếm ngược thời hạn xử lý (SLA).
- **Bảng điều khiển & Thống kê (Dashboards):**
  - **Admin**: Quản lý tài khoản, xem nhật ký truy cập toàn bộ hệ thống (System Logs), thống kê tổng quan.
  - **Leader**: Chuyên trang lưới phân công công việc (Assignment) và cân bằng tải nhân sự.
  - **Staff**: Giao diện tập trung hóa công việc cá nhân (My Queue), nhật ký xử lý chuyên biệt.
- **Hệ thống Đánh giá & Phản hồi (Feedback System):**
  - Nghiệm thu, xếp hạng (Rating 1-5 sao) và để lại đánh giá sau khi Kỹ thuật viên hoàn tất yêu cầu.

---

## 🚀 Hướng dẫn Cài đặt & Khởi chạy

### 1. Chuẩn bị môi trường
Yêu cầu hệ thống đã cài đặt sẵn **Python 3.8+** và Git. Thực hiện sao chép mã nguồn:

```bash
git clone <repository-url>
cd ticket-system-flask
```

### 2. Thiết lập Môi trường Ảo (Virtual Environment)
Khuyến nghị sử dụng môi trường ảo để không gây xung đột thư viện:

```bash
# Tạo môi trường ảo (venv)
python -m venv venv

# Kích hoạt trên Windows
venv\Scripts\activate

# Kích hoạt trên macOS/Linux
source venv/bin/activate
```

### 3. Cài đặt các gói phụ thuộc (Dependencies)
```bash
pip install -r requirements.txt
```

### 4. Thiết lập Cơ sở dữ liệu
Hệ thống sử dụng SQLite mặc định. Các tài khoản thử nghiệm của các Role đã được thiết lập sẵn trong tệp `instance/tickets.db` (nếu đã có). 

> **Tài khoản dùng thử mặc định** (Sử dụng chung Password: `password` hoặc `123456` đối với toàn bộ tài khoản bên dưới):
> - **Admin:** `admin`
> - **Chỉ huy (Leader):** `leader`
> - **Nhân viên (Staff):** `staff`
> - **Người dùng (User):** `user`

### 5. Khởi động Ứng dụng
Khởi chạy Server Flask bằng lệnh:

```bash
python run.py
```
*Truy cập ứng dụng tại trình duyệt: `http://127.0.0.1:5000`*

---

## 📁 Cấu trúc Mã nguồn (Project Structure)

Dự án được ứng dụng mô hình kiến trúc Module chuyên biệt trên Flask, đảm bảo Clean Code và Dễ dàng Scale:

```text
ticket-system-flask/
├── app/                      
│   ├── models/               # Chứa các Model định nghĩa Database (User, Ticket, Interaction...)
│   ├── routes/               # Controllers xử lý Logic tương ứng với từng Role (admin.py, staff.py...)
│   ├── static/               # Tài nguyên tĩnh và CSS framework
│   ├── templates/            # Giao diện Jinja2 HTML (Phân tách theo từng logic Role riêng biệt)
│   ├── __init__.py           # Application Factory Setup
│   └── extensions.py         # Khởi tạo db, login_manager, migrate...
├── instance/                 # Thư mục lưu trữ SQLite Database / File cấu hình nhạy cảm
├── migrations/               # Thư mục chứa lịch sử Flask-Migrate
├── config.py                 # Thông số cấu hình chung cho dự án
├── requirements.txt          # Danh sách thư viện Python
└── run.py                    # Entry point để chạy ứng dụng
```

---

*Phát triển và hoàn thiện dành cho môn học Công nghệ phần mềm (ITSP)*
