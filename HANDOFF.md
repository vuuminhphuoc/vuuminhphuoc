# HANDOFF — Hệ thống Portfolio Hợp Nhất (Góc nhìn từ `vuuminhphuoc`)

> **Cập nhật:** 2026-09-16  
> **Repository:** `vuuminhphuoc/vuuminhphuoc` (GitHub Profile Special Repository)  
> **Ứng viên:** Vưu Minh Phước (Full-Stack Developer, 5+ năm kinh nghiệm, Cà Mau, UTC+7)  
> **Mục tiêu:** Bàn giao quy trình render thẻ profile GitHub, cách đồng bộ từ `my-portfolio` và mối liên kết với 3 repository còn lại.

---

## 1. Bản Đồ 4 Repository Liên Kết

| Repository | Đường dẫn cục bộ | Vai trò và nhiệm vụ |
| :--- | :--- | :--- |
| **`vuuminhphuoc`** *(Repo này)* | `C:\Users\ADMIN\Documents\GitHub\vuuminhphuoc` | **Mặt Tiền GitHub Profile**: Chứa `README.md` hiển thị thẻ SVG terminal phong cách lập trình viên (`light_mode.svg` & `dark_mode.svg`) với chân dung ASCII và số liệu GitHub trực tiếp. |
| **`my-portfolio`** | `C:\Users\ADMIN\Documents\GitHub\my-portfolio` | **Hub Trung Tâm & Nguồn Sự Thật**: Quản lý file gốc `data/profile.json`, website trưng bày Hugo Blox, xuất bản CV PDF (`resume.pdf`), và script điều phối đồng bộ. |
| **`career-ops`** | `C:\Users\ADMIN\Documents\GitHub\career-ops` | **Săn Việc & Bằng Chứng Nội Bộ**: Pipeline đánh giá JD, tạo CV may đo, lưu trữ bảng kiểm kê 85 repository và bằng chứng đóng góp kỹ thuật. |
| **`openshorts`** | `C:\Users\ADMIN\Documents\GitHub\openshorts` | **Sản Xuất Video Demo & Case Study**: Công cụ bridge CLI (`portfolio/showcase.py`) sinh kịch bản quay 9:16, điều phối render qua API local và xuất clip vào website portfolio. |

---

## 2. Cơ Chế Hoạt Động & Quy Trình Render Tại `vuuminhphuoc`

Thư mục này chịu trách nhiệm hiển thị trang cá nhân GitHub (`github.com/vuuminhphuoc`):

1. **Nguồn dữ liệu hồ sơ (`profile.json`)**:
   - Nhận bản chụp chuẩn hóa từ `my-portfolio/data/profile.json` thông qua lệnh đồng bộ `python scripts/sync-profile.py`.
2. **Bộ render ngoại tuyến (`render_profile.py`)**:
   - Chạy 100% bằng thư viện chuẩn Python (Standard Library: `xml.etree.ElementTree`, `json`, `pathlib`).
   - Cập nhật thông tin cá nhân chuẩn xác: Họ tên, vai trò Full-Stack Developer, kinh nghiệm 5+ năm, địa điểm Cà Mau (UTC+7), trạng thái nhận việc Remote 100%, email `vuuminhphuoc@gmail.com`, số điện thoại, và link portfolio `https://vuuminhphuoc-portfolio.netlify.app/`.
   - **Bảo toàn tuyệt đối**:
     - Toàn bộ tranh chân dung ASCII bên trái (x=15).
     - Toàn bộ các thẻ số liệu động do `today.py` cập nhật (repos, stars, commits, followers, LOC).
     - Khung canvas cố định `985x530px` không vỡ bố cục trên GitHub.
3. **Cập nhật `README.md`**:
   - Giữ nguyên thẻ `<picture>` chứa link ảnh SVG theo quy tắc `AGENTS.md`.
   - Cập nhật thẻ `<a>` bên ngoài trỏ thẳng về website chính thức: `https://vuuminhphuoc-portfolio.netlify.app/`.
4. **Tích hợp CI/CD (`.github/workflows/build.yaml`)**:
   - Đã cấu hình bước chạy `python render_profile.py` ngay sau `python today.py` trước khi commit, đảm bảo cron chạy hàng ngày không bao giờ làm mất thông tin hồ sơ mới.

---

## 3. Lệnh Vận Hành & Kiểm Tra Cục Bộ

- **Chạy cập nhật thẻ SVG và README tại chỗ**:
  ```bash
  cd C:\Users\ADMIN\Documents\GitHub\vuuminhphuoc
  python render_profile.py
  ```
- **Cập nhật đồng bộ từ Hub trung tâm**:
  ```bash
  cd C:\Users\ADMIN\Documents\GitHub\my-portfolio
  pnpm run profile:refresh
  ```
