# Midicoder WebGUI API

API Server cho Midicoder WebGUI - CLI Wrapper bằng FastAPI.

## 🎯 Mục đích

API đóng vai trò cầu nối giữa WebGUI (Angular frontend) và Midicoder CLI, cung cấp HTTP endpoints để gọi các commands CLI.

## 📋 Yêu cầu

- Python 3.11+
- Các dependencies trong `requirements.txt`

## 🚀 Cài đặt

```bash
# Cài đặt dependencies
pip install -r requirements.txt
```

## ⚡ Khởi động

### Trước tiên: Init dự án (bắt buộc)

API load CWD từ file `~/.midicoder/midicoder.json`. File này được tạo bởi command `midicoder init`:

```bash
midicoder init
```

### Cách 1: Dùng script (khuyến nghị)

```bash
# Windows
start_api.bat
```

### Cách 2: Chạy bằng terminal

```bash
cd api
set PYTHONPATH=%cd%;%PYTHONPATH%
python -m uvicorn app.main:app --host 0.0.0.0 --port 6868
```

## 🌐 Truy cập

| URL | Mô tả |
|-----|-------|
| http://localhost:6868/docs | Swagger UI (interative testing) |
| http://localhost:6868/redoc | ReDoc documentation |
| http://localhost:6868/api/health/status | Kiểm tra status và CWD |

## 🔌 Endpoints

### Health
| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/api/health/` | Health check |
| GET | `/api/health/ready` | Ready check |
| GET | `/api/health/info` | API info |
| GET | `/api/health/languages` | Danh sách ngôn ngữ |
| GET | `/api/health/status` | Status và CWD hiện tại |

### Config
| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/api/config/list` | Liệt kê config |
| GET | `/api/config/get/{key}` | Lấy giá trị config |
| POST | `/api/config/set` | Đặt giá trị config |
| POST | `/api/config/validate` | Validate config |
| POST | `/api/config/reset` | Reset config |

### Index
| Method | Endpoint | Mô tả |
|--------|----------|-------|
| POST | `/api/index/` | Build index |
| POST | `/api/index/reindex` | Reindex files |

### Version
| Method | Endpoint | Mô tả |
|--------|----------|-------|
| POST | `/api/version/create` | Tạo phiên bản mới |

### Brief
| Method | Endpoint | Mô tả |
|--------|----------|-------|
| POST | `/api/brief/analyze` | Phân tích brief |
| POST | `/api/brief/rewrite` | Viết lại brief |

### Contract
| Method | Endpoint | Mô tả |
|--------|----------|-------|
| POST | `/api/contract/gen` | Generate contract |
| POST | `/api/contract/gen/resume` | Resume contract gen |
| POST | `/api/contract/check` | Kiểm tra contract |
| POST | `/api/contract/feedback` | Feedback cho contract |

### IR
| Method | Endpoint | Mô tả |
|--------|----------|-------|
| POST | `/api/ir/build` | Build MIR |

### Code
| Method | Endpoint | Mô tả |
|--------|----------|-------|
| POST | `/api/code/build` | Build code plan |
| POST | `/api/code/plan` | Plan code |
| POST | `/api/code/gen` | Generate code |
| POST | `/api/code/apply` | Apply code |

### Runtime
| Method | Endpoint | Mô tả |
|--------|----------|-------|
| POST | `/api/runtime/test` | Test runtime |
| POST | `/api/runtime/fix` | Fix runtime errors |

## 🌍 Đa ngôn ngữ (i18n)

API hỗ trợ 2 ngôn ngữ:
- **Tiếng Việt (vi)** - Mặc định
- **Tiếng Anh (en)**

Override ngôn ngữ bằng header:
```bash
curl -H "X-Lang: en" http://localhost:6868/
```

## 📁 Cấu trúc

```
api/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application
│   ├── config.py        # Cấu hình + load CWD
│   ├── i18n.py          # Đa ngôn ngữ
│   ├── models.py        # Pydantic models
│   ├── cli_wrapper.py   # CLI wrapper
│   └── routers/
│       ├── __init__.py
│       ├── health.py
│       ├── config.py
│       ├── index.py
│       ├── version.py
│       ├── brief.py
│       ├── contract.py
│       ├── ir.py
│       ├── code.py
│       └── runtime.py
├── requirements.txt
├── start_api.bat
└── README.md
```

## 🔧 Đổi CWD

API chỉ làm việc trên một CWD duy nhất cùng lúc. Để đổi CWD:

```bash
midicoder config set cwd "new-project-path"
```

Sau đó restart API server.

## 🧪 Test

```bash
# Kiểm tra status và CWD
curl http://localhost:6868/api/health/status

# Test i18n - Tiếng Anh
curl -H "X-Lang: en" http://localhost:6868/

# Test health check
curl http://localhost:6868/api/health/
```

## 📝 Lưu ý

- **Không có endpoint `/api/init/`**: User phải chạy `midicoder init` bằng CLI trước khi dùng API
- API load CWD tự động từ `~/.midicoder/midicoder.json`
- CLI wrapper thuần túy, không thêm logic business
- Tất cả comment trong code bằng tiếng Việt

## 📄 License

MIT