# IT Ticket Management System

Một hệ thống quản lý vé hỗ trợ CNTT đơn giản được xây dựng bằng Flask.

## Tính năng

- **Quản lý người dùng**: Đăng ký, Đăng nhập, Phân quyền (Admin, Leader, Staff, User).
- **Quản lý vé**: Tạo, Phân công, Cập nhật trạng thái, Bình luận.
- **Thống kê**: Dashboard thống kê số lượng vé theo trạng thái và thời gian.
- **Thông báo**: Thông báo thời gian thực về cập nhật vé.

## Cài đặt

1.  **Clone repository** (hoặc giải nén source code):
    ```bash
    git clone <repository-url>
    cd ticket-system-flask
    ```

2.  **Tạo môi trường ảo (Khuyên dùng)**:
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **Cài đặt thư viện**:
    ```bash
    pip install -r requirements.txt
    ```

## Khởi tạo Cơ sở dữ liệu

Trước khi chạy ứng dụng lần đầu, bạn cần khởi tạo cơ sở dữ liệu và tạo các tài khoản mặc định.

```bash
python init_db.py
```

Lệnh này sẽ tạo file `instance/tickets.db` và tạo các tài khoản mẫu:

| Role   | Username | Password |
| :----- | :------- | :------- |
| Admin  | admin    | password |
| Leader | leader   | password |
| Staff  | staff    | password |
| User   | user     | password |

## Chạy ứng dụng

```bash
python app.py
```

Truy cập ứng dụng tại chuyển trình duyệt: `http://127.0.0.1:5000`

## Cấu trúc dự án

- `app.py`: Điểm khởi chạy ứng dụng.
- `config.py`: Cấu hình hệ thống.
- `models.py`: Định nghĩa cơ sở dữ liệu (User, Ticket, Notification, v.v.).
- `routes/`: Các controllers xử lý logic cho từng vai trò.
- `templates/`: Giao diện HTML (Jinja2).
- `static/`: File tĩnh (CSS, JS, Images).
