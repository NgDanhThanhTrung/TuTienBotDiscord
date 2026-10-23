"""Dữ liệu tĩnh của game Tu Tiên: cảnh giới, linh căn, vật phẩm, yêu thú."""

# ---------------------------------------------------------------------------
# CẢNH GIỚI
#   yeu_cau : Linh lực cần có để ĐỘT PHÁ lên cảnh giới kế tiếp
#   ti_le   : Tỉ lệ đột phá thành công cơ bản (0.80 = 80%)
#   mau     : Màu viền Embed
# Cảnh giới cuối cùng (Đại Thừa) là đỉnh cao, không thể đột phá thêm.
# ---------------------------------------------------------------------------
CANH_GIOI = [
    {"ten": "Luyện Khí", "yeu_cau": 300,     "ti_le": 0.80, "mau": 0x95A5A6},
    {"ten": "Trúc Cơ",   "yeu_cau": 1_500,   "ti_le": 0.65, "mau": 0x2ECC71},
    {"ten": "Kim Đan",   "yeu_cau": 6_000,   "ti_le": 0.50, "mau": 0xF1C40F},
    {"ten": "Nguyên Anh", "yeu_cau": 20_000, "ti_le": 0.40, "mau": 0xE67E22},
    {"ten": "Hóa Thần",  "yeu_cau": 70_000,  "ti_le": 0.30, "mau": 0xE74C3C},
    {"ten": "Luyện Hư",  "yeu_cau": 200_000, "ti_le": 0.22, "mau": 0x9B59B6},
    {"ten": "Hợp Thể",   "yeu_cau": 600_000, "ti_le": 0.15, "mau": 0x3498DB},
    {"ten": "Đại Thừa",  "yeu_cau": 0,       "ti_le": 0.00, "mau": 0xFFD700},
]
CANH_GIOI_TOI_DA = len(CANH_GIOI) - 1

# ---------------------------------------------------------------------------
# LINH CĂN (random khi tạo nhân vật)
#   he_so    : nhân lên Linh lực nhận được khi tu luyện
#   ti_trong : trọng số random
# ---------------------------------------------------------------------------
LINH_CAN = {
    "Thiên Linh Căn": {"he_so": 1.5,  "ti_trong": 5},
    "Địa Linh Căn":   {"he_so": 1.25, "ti_trong": 15},
    "Nhân Linh Căn":  {"he_so": 1.0,  "ti_trong": 40},
    "Ngụy Linh Căn":  {"he_so": 0.8,  "ti_trong": 40},
}

# ---------------------------------------------------------------------------
# HẰNG SỐ CÂN BẰNG GAME (chỉnh ở đây cho dễ)
# ---------------------------------------------------------------------------
TU_LUYEN_CD = 60                  # giây hồi chiêu tu luyện
NHIEM_VU_CD = 120                 # giây hồi chiêu làm nhiệm vụ
TU_LUYEN_LINH_LUC = (25, 45)      # khoảng Linh lực mỗi lần tu luyện (cảnh giới 0)
HE_SO_LINH_LUC = 3.0              # mỗi cảnh giới, Linh lực nhận được nhân thêm 3 lần
NHIEM_VU_LINH_LUC = (40, 90)
NHIEM_VU_LINH_THACH = (15, 40)
HE_SO_LINH_THACH = 1.8            # mỗi cảnh giới, Linh thạch nhận được nhân thêm 1.8 lần
THAT_BAI_MAT_LINH_LUC = 0.30      # đột phá thất bại: mất 30% Linh lực hiện có

TRUC_CO_DAN_BONUS = 0.20          # +20% tỉ lệ đột phá
TU_KHI_DAN_LINH_LUC = 500         # +500 Linh lực
TU_LINH_PHU_GIAM_CD = 0.5         # giảm 50% hồi chiêu
TU_LINH_PHU_THOI_GIAN = 600       # Tụ Linh Phù có hiệu lực 10 phút

# ---------------------------------------------------------------------------
# VẬT PHẨM
# ---------------------------------------------------------------------------
VAT_PHAM = {
    "truc_co_dan": {
        "ten": "Trúc Cơ Đan",
        "emoji": "💊",
        "mo_ta": "Tăng +20% tỉ lệ đột phá lần kế tiếp.",
        "gia_mua": 200,
        "gia_ban": 80,
    },
    "tu_khi_dan": {
        "ten": "Tụ Khí Đan",
        "emoji": "🟠",
        "mo_ta": "Tăng ngay +500 Linh lực khi dùng.",
        "gia_mua": 60,
        "gia_ban": 25,
    },
    "tu_linh_phu": {
        "ten": "Tụ Linh Phù",
        "emoji": "📜",
        "mo_ta": "Giảm 50% hồi chiêu tu luyện trong 10 phút.",
        "gia_mua": 100,
        "gia_ban": 40,
    },
}

# ---------------------------------------------------------------------------
# YÊU THÚ (nhiệm vụ săn yêu thú) - min_realm: cảnh giới thấp nhất gặp được
# ---------------------------------------------------------------------------
YEU_THU = [
    {"ten": "Sói Linh Hoang",        "min_realm": 0},
    {"ten": "Nhện Độc Thạch Quật",   "min_realm": 0},
    {"ten": "Hắc Xà Yêu",            "min_realm": 1},
    {"ten": "Hỏa Dực Điêu",          "min_realm": 2},
    {"ten": "Huyền Quy Vạn Niên",    "min_realm": 3},
    {"ten": "Cửu Vĩ Hồ Yêu",         "min_realm": 4},
    {"ten": "Ma Long Hư Không",      "min_realm": 5},
    {"ten": "Thôn Thiên Tà Thú",     "min_realm": 6},
]

# Tỉ lệ rơi vật phẩm khi làm nhiệm vụ: (id vật phẩm, xác suất)
NHIEM_VU_DROP = [
    ("truc_co_dan", 0.03),
    ("tu_linh_phu", 0.07),
    ("tu_khi_dan", 0.15),
]
