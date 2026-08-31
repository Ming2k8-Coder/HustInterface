# 🎓 HUST Interface - High-Performance MCP Server & Crawler

> **Model Context Protocol (MCP) Server** và bộ công cụ thu thập dữ liệu (Crawler/API Client) hiệu năng cao dành cho các cổng dịch vụ sinh viên **Đại học Bách khoa Hà Nội (HUST)**: **iCTSV**, **eHUST / QLĐT**, và **CTMS**.

---

## 🚀 Tính năng chính

### 1. 📋 iCTSV (Cổng Công tác Sinh viên)
- 🏅 **Điểm rèn luyện (ĐRL)**: Tra cứu điểm rèn luyện tổng kết và chi tiết từng nhóm tiêu chí (ý thức học tập, chấp hành nội quy, hoạt động ngoại khóa,...).
- 🎯 **Hoạt động ngoại khóa**: Liệt kê các hoạt động đang mở đăng ký, sắp diễn ra, số lượng người tham gia, điểm cộng.
- ✍️ **Đăng ký hoạt động**: Tự động gửi yêu cầu đăng ký tham gia sự kiện CTSV.
- 📌 **Lịch sử đăng ký & Điểm danh**: Kiểm tra các hoạt động đã đăng ký và trạng thái tham dự.
- 🔔 **Thông báo CTSV**: Nhận thông báo mới nhất từ Ban CTSV.

### 2. 📅 eHUST & QLĐT (Cổng Quản lý Đào tạo)
- 👤 **Thông tin sinh viên**: Họ tên, MSSV, lớp sinh viên, khoa/viện, ngành học, chương trình đào tạo.
- 🗓️ **Thời khóa biểu tuần**: Lịch học chi tiết theo tuần học/học kỳ, phòng học (D9, TC, B1,...), kíp học, giảng viên.
- 📊 **Bảng điểm & CPA/GPA**: Bảng điểm chi tiết từng môn (điểm quá trình, điểm thi, điểm chữ) và CPA tích lũy.
- 📝 **Lịch thi học kỳ**: Ngày thi, ca thi/kíp thi, phòng thi, số báo danh.

### 3. 📚 CTMS (Cổng học phần Moodle & Đồ án)
- 📖 **Lớp học phần**: Danh sách các môn học và tài liệu giảng dạy trên CTMS.
- ⏰ **Bài tập & Hạn nộp**: Tra cứu các bài tập, đề tài đồ án và deadline sắp tới.

### 4. ⚡ Hiệu năng & Cơ chế Xác thực
- **Tốc độ tối đa**: Xây dựng trên nền tảng **`uv`**, **`httpx`** (HTTP/2 multiplexing, async connection pool), và parser **`lxml`**.
- **Cơ chế lưu trữ phiên (Session Cache)**: Lưu token/cookies cục bộ tại `~/.hust_interface/session_cache.json` để các lệnh MCP trả lời gần như tức thì mà không cần bật lại trình duyệt.
- **Linh hoạt đăng nhập**:
  1. Tự động qua Microsoft SSO (`hust-mcp login-sso` với Playwright Headless).
  2. Hoặc nhập Token/Cookie thủ công (`hust-mcp set-token` hoặc file `.env`).

---

## 🛠️ Cài đặt & Khởi động nhanh

Dự án sử dụng trình quản lý gói siêu nhanh **`uv`**:

```bash
# 1. Cài đặt dependencies
uv sync

# 2. Xem hướng dẫn CLI
uv run hust-mcp --help

# 3. Kiểm tra trạng thái đăng nhập
uv run hust-mcp status
```

---

## 🔐 Cấu hình Xác thực Trực tiếp (Né Microsoft SSO)

Hệ thống sử dụng trực tiếp các cổng xác thực nội bộ của HUST:
1. **eHUST (Pure HTTP - Không cần trình duyệt)**: `https://e.hust.edu.vn/sso/login`
2. **iCTSV / CTSV (Direct API & Form)**: `https://ctsv.hust.edu.vn/#/login` (API: `https://ctsv.hust.edu.vn/api-t`)

### 1. Đăng nhập eHUST (Pure HTTP)
```bash
uv run hust-mcp login-ehust --email "your_email@sis.hust.edu.vn"
```

### 2. Đăng nhập CTSV (Direct Form)
```bash
uv run hust-mcp login-ctsv --email "your_mssv_or_email"
```

### 3. Đăng nhập cả 2 cùng lúc:
```bash
uv run hust-mcp login-all --email "minh.nt2611037@sis.hust.edu.vn"
```

### 4. Hoặc Cấu hình Token / Cookie thủ công (Tức thì, 0ms)
```bash
uv run hust-mcp set-token ictsv "Bearer eyJhbGci..."
uv run hust-mcp set-token ehust "JSESSIONID=..."
```


---

## 🔌 Cấu hình kết nối MCP Client

### 1. Claude Desktop (`claude_desktop_config.json`)

```json
{
  "mcpServers": {
    "hust-interface": {
      "command": "uv",
      "args": [
        "--directory",
        "E:\\Master_Project\\Coder_projext\\HustInterface",
        "run",
        "hust-mcp",
        "run"
      ],
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

### 2. Cursor / Antigravity / Windsurf
Sử dụng file [mcp.json](file:///e:/Master_Project/Coder_projext/HustInterface/mcp.json) có sẵn trong thư mục gốc của dự án.

---

## 🧰 Danh sách MCP Tools có sẵn

| Tên Tool | Mô tả |
| :--- | :--- |
| `hust_check_auth_status` | Kiểm tra trạng thái đăng nhập các dịch vụ |
| `hust_set_token` | Nhập token hoặc cookie cho `ictsv`, `ehust`, `ctms` |
| `hust_login_sso` | Đăng nhập Microsoft SSO tự động bằng Headless Browser |
| `hust_clear_session` | Xóa session cache / đăng xuất |
| `hust_summarize_student` | **All-in-one:** Tổng hợp toàn diện Profile, CPA, GPA, ĐRL, Lịch thi, Nợ học phí, Cảnh báo học tập |
| `ictsv_get_training_points` | Lấy điểm rèn luyện tổng kết và chi tiết từng tiêu chí theo kỳ |
| `ictsv_get_drl_history` | Lấy lịch sử Điểm rèn luyện qua tất cả các học kỳ |
| `ictsv_get_student_contact` | Lấy thông tin liên hệ sinh viên (SĐT, địa chỉ, liên hệ khẩn cấp) |
| `ictsv_get_activities` | Danh sách hoạt động ngoại khóa mở đăng ký, lọc theo điểm ĐRL / nhóm tiêu chí |
| `ictsv_register_activity` | Đăng ký tham gia hoạt động CTSV |
| `ictsv_get_my_activities` | Danh sách hoạt động sinh viên đã đăng ký |
| `ictsv_get_notifications` | Lấy thông báo mới nhất từ Ban CTSV |
| `ictsv_search_jobs` | Tìm kiếm cơ hội việc làm, thực tập doanh nghiệp trên HUST Career |
| `ehust_get_student_profile` | Lấy thông tin cá nhân sinh viên, lớp, ngành đào tạo |
| `ehust_get_schedule` | Lấy thời khóa biểu học tập theo tuần & học kỳ |
| `ehust_get_grades` | Tra cứu bảng điểm chi tiết, GPA, CPA |
| `ehust_get_all_semesters_grades` | Tra cứu điểm toàn bộ các học kỳ từ trước tới nay |
| `ehust_get_exam_schedule` | Lấy lịch thi học kỳ (kíp thi, phòng thi, SBD) |
| `ehust_get_upcoming_exams` | Lọc danh sách các môn thi sắp diễn ra trong vòng N ngày tới |
| `ehust_get_tuition` | Tra cứu học phí, số tiền đã đóng và tình trạng nợ học phí |
| `ehust_get_registration_plan` | Kế hoạch đăng ký học phần / khung chương trình gợi ý |
| `ehust_get_course_syllabus` | Tra cứu Đề cương chi tiết học phần, mô tả tóm tắt, giáo trình, slide bài giảng & file tải về |
| `ehust_check_graduation_eligibility` | Kiểm tra điều kiện tốt nghiệp (tín chỉ tích lũy, CPA tối thiểu) |
| `ctms_get_enrolled_courses` | Lấy danh sách môn học trên CTMS (Moodle) |

| `ctms_get_assignments` | Tra cứu danh sách bài tập & đồ án trên CTMS |
| `ctms_get_upcoming_deadlines` | Lọc các deadline bài tập cần nộp trong vòng N ngày tới |

---

### 💡 MCP Prompts
- **`daily_student_briefing`**: Tóm tắt lịch học hôm nay, hạn nộp bài tập CTMS và hoạt động CTSV.
- **`academic_evaluation`**: Đánh giá chi tiết kết quả học tập, CPA/GPA và đề xuất kế hoạch cải thiện.
- **`weekly_study_planner`**: Lập kế hoạch học tập chi tiết trong tuần dựa trên thời khóa biểu, lịch thi và deadline.
- **`academic_risk_alert`**: Cảnh báo rủi ro học thuật (GPA thấp, thiếu ĐRL, nợ học phí, nguy cơ cảnh cáo).


---

## 🧪 Kiểm thử (Testing)

Chạy bộ unit test tự động với pytest:

```bash
uv run pytest -v
```

---

## 📁 Cấu trúc thư mục

```
HustInterface/
├── pyproject.toml              # Cấu hình project uv & dependencies
├── mcp.json                    # Cấu hình kết nối MCP Server
├── .env.example                # File mẫu biến môi trường
├── README.md                   # Tài liệu hướng dẫn
├── tests/                      # Bộ kiểm thử pytest
│   ├── test_models.py
│   ├── test_session_manager.py
│   └── test_server_tools.py
└── src/
    └── hust_interface/
        ├── config.py           # Quản lý cấu hình & Pydantic Settings
        ├── server.py           # Khởi tạo MCP Server, Resources & Prompts
        ├── cli.py              # Giao diện dòng lệnh CLI (hust-mcp)
        ├── core/               # Http Client (async) & Quản lý Session
        ├── auth/               # Microsoft SSO & Manual Auth
        ├── models/             # Định nghĩa Pydantic Models kiểu dữ liệu
        ├── crawlers/           # Module Crawler cho iCTSV, eHUST, CTMS
        └── tools/              # Đăng ký MCP Tools cho từng phân hệ
```

---

## 🤝 Liên quan & Cảm hứng (Related Projects)

- [zennomi/sanbaka](https://github.com/zennomi/sanbaka): Dự án AI Companion / Bạn gái AI dành cho sinh viên Bách Khoa (HUST) - nơi khởi nguồn ý tưởng về việc tương tác và theo dõi Điểm Rèn Luyện (ĐRL) cho sinh viên HUST.
