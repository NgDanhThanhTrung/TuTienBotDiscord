"""Toàn bộ logic game. Mọi hàm trả về (thanh_cong: bool, thong_bao: str)."""

import random
import time

from database import get_lock, lay_nguoi_choi, players
from game_data import (
    CANH_GIOI,
    CANH_GIOI_TOI_DA,
    HE_SO_LINH_LUC,
    HE_SO_LINH_THACH,
    LINH_CAN,
    NHIEM_VU_CD,
    NHIEM_VU_DROP,
    NHIEM_VU_LINH_LUC,
    NHIEM_VU_LINH_THACH,
    THAT_BAI_MAT_LINH_LUC,
    TRUC_CO_DAN_BONUS,
    TU_KHI_DAN_LINH_LUC,
    TU_LINH_PHU_GIAM_CD,
    TU_LINH_PHU_THOI_GIAN,
    TU_LUYEN_CD,
    TU_LUYEN_LINH_LUC,
    VAT_PHAM,
    YEU_THU,
)


# ===========================================================================
# Hàm hỗ trợ
# ===========================================================================
async def _tru_vat_pham(user_id: int, item_id: str) -> bool:
    """Trừ 1 vật phẩm trong túi (nguyên tử). Trả False nếu không đủ."""
    truong = f"tui_do.{item_id}"
    kq = await players().find_one_and_update(
        {"user_id": user_id, truong: {"$gte": 1}},
        {"$inc": {truong: -1}},
    )
    if kq is None:
        return False
    # Dọn rác: số lượng về 0 thì xóa khỏi túi
    await players().update_one(
        {"user_id": user_id, truong: {"$lte": 0}},
        {"$unset": {truong: ""}},
    )
    return True


# ===========================================================================
# TU LUYỆN
# ===========================================================================
async def tu_luyen(user_id: int):
    async with get_lock(user_id):
        p = await lay_nguoi_choi(user_id)
        now = time.time()

        con_lai = p["cooldown"].get("tu_luyen", 0) - now
        if con_lai > 0:
            return False, f"⏳ Linh khí chưa hồi phục, đợi **{int(con_lai) + 1}s** nữa."

        canh_gioi = p["canh_gioi"]
        he_so_can = LINH_CAN.get(p["linh_can"], {"he_so": 1.0})["he_so"]
        gain = int(
            random.randint(*TU_LUYEN_LINH_LUC)
            * (HE_SO_LINH_LUC ** canh_gioi)
            * he_so_can
        )

        cd = TU_LUYEN_CD
        co_phu = p["buff"].get("tu_linh_phu_den", 0) > now
        if co_phu:
            cd = int(cd * (1 - TU_LINH_PHU_GIAM_CD))

        await players().update_one(
            {"user_id": user_id},
            {
                "$inc": {"linh_luc": gain},
                "$set": {"cooldown.tu_luyen": now + cd},
            },
        )

        msg = f"🧘 Đạo hữu ngồi thiền hấp thụ linh khí, **+{gain:,} Linh lực**."
        if co_phu:
            msg += f"\n📜 Tụ Linh Phù phát huy tác dụng: hồi chiêu chỉ còn **{cd}s**."
        return True, msg


# ===========================================================================
# ĐỘT PHÁ
# ===========================================================================
async def dot_pha(user_id: int):
    async with get_lock(user_id):
        p = await lay_nguoi_choi(user_id)
        canh_gioi = p["canh_gioi"]

        if canh_gioi >= CANH_GIOI_TOI_DA:
            return False, "🌟 Đạo hữu đã đăng đỉnh, không còn cảnh giới nào để đột phá!"

        cg = CANH_GIOI[canh_gioi]
        if p["linh_luc"] < cg["yeu_cau"]:
            return False, f"❌ Linh lực chưa đủ **{cg['yeu_cau']:,}** để đột phá!"

        bonus = p["buff"].get("dot_pha", 0.0)
        ti_le = min(0.95, cg["ti_le"] + bonus)

        if random.random() < ti_le:
            moi = CANH_GIOI[canh_gioi + 1]["ten"]
            await players().update_one(
                {"user_id": user_id},
                {
                    "$inc": {"canh_gioi": 1, "linh_luc": -cg["yeu_cau"]},
                    "$set": {"buff.dot_pha": 0.0},
                },
            )
            return True, (
                f"⚡ **ĐỘT PHÁ THÀNH CÔNG!** Thiên địa dị tượng, đạo hữu tiến vào "
                f"cảnh giới **{moi}**! (tỉ lệ {ti_le:.0%})"
            )

        mat = int(p["linh_luc"] * THAT_BAI_MAT_LINH_LUC)
        await players().update_one(
            {"user_id": user_id},
            {
                "$inc": {"linh_luc": -mat},
                "$set": {"buff.dot_pha": 0.0},
            },
        )
        return False, (
            f"💥 **ĐỘT PHÁ THẤT BẠI!** Linh khí phản phệ, mất **{mat:,} Linh lực**. "
            f"(tỉ lệ {ti_le:.0%})"
        )


# ===========================================================================
# LÀM NHIỆM VỤ (SĂN YÊU THÚ)
# ===========================================================================
async def lam_nhiem_vu(user_id: int):
    async with get_lock(user_id):
        p = await lay_nguoi_choi(user_id)
        now = time.time()

        con_lai = p["cooldown"].get("nhiem_vu", 0) - now
        if con_lai > 0:
            return False, f"⏳ Đạo hữu đang trọng thương, nghỉ ngơi **{int(con_lai) + 1}s** nữa."

        r = p["canh_gioi"]
        ung_vien = [t for t in YEU_THU if r - 2 <= t["min_realm"] <= r]
        thu = random.choice(ung_vien)

        linh_thach = int(random.randint(*NHIEM_VU_LINH_THACH) * (HE_SO_LINH_THACH ** r))
        linh_luc = int(random.randint(*NHIEM_VU_LINH_LUC) * (HE_SO_LINH_LUC ** r))

        cap_nhat = {"linh_thach": linh_thach, "linh_luc": linh_luc}
        roi_text = ""
        roll = random.random()
        tich_luy = 0.0
        for item_id, xac_suat in NHIEM_VU_DROP:
            tich_luy += xac_suat
            if roll < tich_luy:
                cap_nhat[f"tui_do.{item_id}"] = 1
                vp = VAT_PHAM[item_id]
                roi_text = f"\n🎁 Yêu thú rơi ra **{vp['emoji']} {vp['ten']}**!"
                break

        await players().update_one(
            {"user_id": user_id},
            {
                "$inc": cap_nhat,
                "$set": {"cooldown.nhiem_vu": now + NHIEM_VU_CD},
            },
        )
        return True, (
            f"⚔️ Đạo hữu chém giết **{thu['ten']}**, nhận **+{linh_thach:,} Linh thạch** "
            f"và **+{linh_luc:,} Linh lực**.{roi_text}"
        )


# ===========================================================================
# DÙNG VẬT PHẨM
# ===========================================================================
async def dung_vat_pham(user_id: int, item_id: str):
    vp = VAT_PHAM.get(item_id)
    if vp is None:
        return False, "❌ Vật phẩm không tồn tại."

    async with get_lock(user_id):
        p = await lay_nguoi_choi(user_id)
        now = time.time()

        if p["tui_do"].get(item_id, 0) < 1:
            return False, f"❌ Túi đồ không còn **{vp['ten']}**."

        if item_id == "truc_co_dan":
            if p["canh_gioi"] >= CANH_GIOI_TOI_DA:
                return False, "🌟 Đạo hữu đã đăng đỉnh, không cần Trúc Cơ Đan nữa."
            if p["buff"].get("dot_pha", 0.0) > 0:
                return False, "⚠️ Dược lực Trúc Cơ Đan trước đó vẫn đang có hiệu lực."
            hieu_ung = {"$set": {"buff.dot_pha": TRUC_CO_DAN_BONUS}}
            thong_bao = (
                f"💊 Dùng **Trúc Cơ Đan**, tỉ lệ đột phá lần tới "
                f"**+{TRUC_CO_DAN_BONUS:.0%}**."
            )

        elif item_id == "tu_khi_dan":
            hieu_ung = {"$inc": {"linh_luc": TU_KHI_DAN_LINH_LUC}}
            thong_bao = f"🟠 Dùng **Tụ Khí Đan**, **+{TU_KHI_DAN_LINH_LUC:,} Linh lực**."

        elif item_id == "tu_linh_phu":
            if p["buff"].get("tu_linh_phu_den", 0) > now:
                return False, "⚠️ Tụ Linh Phù trước đó vẫn đang có hiệu lực."
            con_lai = max(0.0, p["cooldown"].get("tu_luyen", 0) - now)
            cd_moi = now + con_lai * (1 - TU_LINH_PHU_GIAM_CD)  # giảm luôn CD đang chạy
            hieu_ung = {
                "$set": {
                    "buff.tu_linh_phu_den": now + TU_LINH_PHU_THOI_GIAN,
                    "cooldown.tu_luyen": cd_moi,
                }
            }
            thong_bao = (
                f"📜 Kích hoạt **Tụ Linh Phù**: hồi chiêu tu luyện giảm "
                f"**{TU_LINH_PHU_GIAM_CD:.0%}** trong {TU_LINH_PHU_THOI_GIAN // 60} phút."
            )
        else:
            return False, "❌ Vật phẩm này chưa có công dụng."

        if not await _tru_vat_pham(user_id, item_id):
            return False, f"❌ Túi đồ không còn **{vp['ten']}**."
        await players().update_one({"user_id": user_id}, hieu_ung)
        return True, thong_bao


# ===========================================================================
# CHỢ ĐEN: MUA / BÁN
# ===========================================================================
async def mua(user_id: int, item_id: str):
    vp = VAT_PHAM.get(item_id)
    if vp is None:
        return False, "❌ Vật phẩm không tồn tại."

    async with get_lock(user_id):
        await lay_nguoi_choi(user_id)
        kq = await players().find_one_and_update(
            {"user_id": user_id, "linh_thach": {"$gte": vp["gia_mua"]}},
            {"$inc": {"linh_thach": -vp["gia_mua"], f"tui_do.{item_id}": 1}},
        )
        if kq is None:
            return False, f"💸 Không đủ Linh thạch! **{vp['ten']}** giá **{vp['gia_mua']:,}** Linh thạch."
        return True, f"🛒 Đã mua **{vp['emoji']} {vp['ten']}** với giá **{vp['gia_mua']:,}** Linh thạch."


async def ban(user_id: int, item_id: str):
    vp = VAT_PHAM.get(item_id)
    if vp is None:
        return False, "❌ Vật phẩm không tồn tại."

    async with get_lock(user_id):
        await lay_nguoi_choi(user_id)
        truong = f"tui_do.{item_id}"
        kq = await players().find_one_and_update(
            {"user_id": user_id, truong: {"$gte": 1}},
            {"$inc": {truong: -1, "linh_thach": vp["gia_ban"]}},
        )
        if kq is None:
            return False, f"❌ Túi đồ không có **{vp['ten']}** để bán."
        await players().update_one(
            {"user_id": user_id, truong: {"$lte": 0}},
            {"$unset": {truong: ""}},
        )
        return True, f"💰 Đã bán **{vp['emoji']} {vp['ten']}**, nhận **{vp['gia_ban']:,}** Linh thạch."
