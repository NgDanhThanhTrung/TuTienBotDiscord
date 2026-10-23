"""Kết nối MongoDB Atlas bằng Motor (async) và các hàm truy xuất người chơi."""

import asyncio
import os
import random

import motor.motor_asyncio

from game_data import LINH_CAN

_client = None
_db = None
_locks: dict[int, asyncio.Lock] = {}


async def ket_noi() -> None:
    """Kết nối tới MongoDB Atlas. Gọi 1 lần khi bot khởi động."""
    global _client, _db
    uri = os.getenv("MONGODB_URI")
    if not uri:
        raise RuntimeError("Thiếu MONGODB_URI trong file .env / biến môi trường!")

    _client = motor.motor_asyncio.AsyncIOMotorClient(
        uri,
        maxPoolSize=10,                 # nhẹ cho RAM 512MB
        serverSelectionTimeoutMS=15000,
    )
    await _client.admin.command("ping")  # kiểm tra kết nối ngay, lỗi sẽ báo sớm
    _db = _client[os.getenv("DB_NAME", "tutien_bot")]
    await _db.players.create_index("user_id", unique=True)
    print("✅ Đã kết nối MongoDB Atlas.")


def players():
    """Trả về collection `players`."""
    return _db.players


def get_lock(user_id: int) -> asyncio.Lock:
    """Mỗi người chơi 1 khóa: tránh bấm nút liên tục gây ghi đè dữ liệu."""
    lock = _locks.get(user_id)
    if lock is None:
        lock = _locks[user_id] = asyncio.Lock()
    return lock


def _random_linh_can() -> str:
    ten = list(LINH_CAN.keys())
    trong_so = [LINH_CAN[k]["ti_trong"] for k in ten]
    return random.choices(ten, weights=trong_so, k=1)[0]


async def lay_nguoi_choi(user_id: int) -> dict:
    """Lấy hồ sơ người chơi; nếu chưa có thì tạo mới (upsert, an toàn khi gọi song song)."""
    ho_so_moi = {
        "linh_can": _random_linh_can(),
        "canh_gioi": 0,        # chỉ số trong CANH_GIOI
        "linh_luc": 0,
        "linh_thach": 100,     # vốn khởi đầu
        "tui_do": {},          # {"item_id": so_luong}
        "buff": {"dot_pha": 0.0, "tu_linh_phu_den": 0},
        "cooldown": {"tu_luyen": 0, "nhiem_vu": 0},
    }
    await players().update_one(
        {"user_id": user_id},
        {"$setOnInsert": ho_so_moi},
        upsert=True,
    )
    return await players().find_one({"user_id": user_id})


async def da_co_nguoi_choi(user_id: int) -> bool:
    """Kiểm tra người chơi đã /start (đã có hồ sơ) chưa."""
    return await players().count_documents({"user_id": user_id}, limit=1) > 0
