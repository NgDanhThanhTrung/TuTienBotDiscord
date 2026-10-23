"""Giao diện Discord: Embed + View + Button + Select.

Nguyên tắc: mỗi thao tác chỉ dùng interaction.response.edit_message()
để cập nhật CHÍNH tin nhắn bảng điều khiển, không gửi tin nhắn mới.
"""

import time

import discord
from discord import ui

import database as db
import game_logic as gl
from game_data import CANH_GIOI, CANH_GIOI_TOI_DA, VAT_PHAM


# ===========================================================================
# EMBED
# ===========================================================================
def _thanh_tien_do(hien_tai: int, can: int, dai: int = 12) -> str:
    ti_le = 1.0 if can <= 0 else min(hien_tai / can, 1.0)
    day = int(ti_le * dai)
    return "▰" * day + "▱" * (dai - day) + f" {ti_le:.0%}"


def embed_chinh(p: dict, user: discord.abc.User, log: str | None = None) -> discord.Embed:
    r = p["canh_gioi"]
    cg = CANH_GIOI[r]
    toi_da = r >= CANH_GIOI_TOI_DA
    now = time.time()

    emb = discord.Embed(
        title=f"☯️ Tu Tiên Giới • {user.display_name}",
        description=log or "*Đại đạo vô thường, hãy chọn một con đường...*",
        color=cg["mau"],
    )
    emb.set_thumbnail(url=user.display_avatar.url)
    emb.add_field(name="🌿 Linh Căn", value=p["linh_can"], inline=True)
    emb.add_field(name="🏔️ Cảnh Giới", value=f"**{cg['ten']}**", inline=True)
    emb.add_field(name="💎 Linh Thạch", value=f"{p['linh_thach']:,}", inline=True)

    if toi_da:
        luc = f"{p['linh_luc']:,} • 🌟 Đã đăng đỉnh"
    else:
        luc = f"{_thanh_tien_do(p['linh_luc'], cg['yeu_cau'])}\n{p['linh_luc']:,} / {cg['yeu_cau']:,}"
    emb.add_field(name="✨ Linh Lực", value=luc, inline=False)

    # Hồi chiêu
    cd_tl = p["cooldown"].get("tu_luyen", 0)
    cd_nv = p["cooldown"].get("nhiem_vu", 0)
    dong_cd = (
        f"🧘 Tu luyện: {f'<t:{int(cd_tl)}:R>' if cd_tl > now else '✅ sẵn sàng'}\n"
        f"⚔️ Nhiệm vụ: {f'<t:{int(cd_nv)}:R>' if cd_nv > now else '✅ sẵn sàng'}"
    )
    emb.add_field(name="⏱️ Hồi chiêu", value=dong_cd, inline=True)

    # Buff đang có
    buffs = []
    if p["buff"].get("dot_pha", 0.0) > 0:
        buffs.append(f"💊 Đột phá +{p['buff']['dot_pha']:.0%}")
    den = p["buff"].get("tu_linh_phu_den", 0)
    if den > now:
        buffs.append(f"📜 Tụ Linh Phù hết hạn <t:{int(den)}:R>")
    emb.add_field(name="🔮 Hiệu ứng", value="\n".join(buffs) or "Không có", inline=True)

    emb.set_footer(text="Gõ /game để mở bảng điều khiển riêng của bạn")
    return emb


def embed_tui(p: dict, user: discord.abc.User, log: str | None = None) -> discord.Embed:
    emb = discord.Embed(
        title=f"🎒 Túi Đồ • {user.display_name}",
        description=log or "Chọn vật phẩm ở menu bên dưới để sử dụng.",
        color=0x3498DB,
    )
    dong = []
    for item_id, sl in p["tui_do"].items():
        vp = VAT_PHAM.get(item_id)
        if vp and sl > 0:
            dong.append(f"{vp['emoji']} **{vp['ten']}** x{sl}\n└ *{vp['mo_ta']}*")
    emb.add_field(name="Vật phẩm", value="\n".join(dong) or "*Túi đồ trống rỗng...*", inline=False)
    emb.add_field(name="💎 Linh Thạch", value=f"{p['linh_thach']:,}", inline=True)
    return emb


def embed_cho_den(p: dict, user: discord.abc.User, log: str | None = None) -> discord.Embed:
    emb = discord.Embed(
        title="🕶️ Chợ Đen",
        description=log or "Lão bản thì thầm: *\"Đan dược chính hiệu, không mặc cả...\"*",
        color=0x2C2F33,
    )
    bang = []
    for vp in VAT_PHAM.values():
        bang.append(
            f"{vp['emoji']} **{vp['ten']}**\n"
            f"└ Mua: **{vp['gia_mua']:,}** 💎 | Bán: **{vp['gia_ban']:,}** 💎\n"
            f"└ *{vp['mo_ta']}*"
        )
    emb.add_field(name="Hàng hóa", value="\n".join(bang), inline=False)
    emb.add_field(name="💎 Linh Thạch của bạn", value=f"{p['linh_thach']:,}", inline=True)
    return emb


# ===========================================================================
# VIEW CƠ SỞ
# ===========================================================================
class OwnerView(ui.View):
    """View chỉ cho phép chủ nhân bảng điều khiển bấm."""

    def __init__(self, owner_id: int, timeout: float = 300):
        super().__init__(timeout=timeout)
        self.owner_id = owner_id
        self.message: discord.Message | None = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "🚫 Đây không phải bảng điều khiển của đạo hữu. Hãy gõ **/game** để mở bảng riêng!",
                ephemeral=True,
            )
            return False
        return True

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass


async def _chuyen_view(
    interaction: discord.Interaction,
    view_cu: OwnerView,
    embed: discord.Embed,
    view_moi: OwnerView,
) -> None:
    """Cập nhật chính tin nhắn bằng edit_message (không spam tin nhắn mới)."""
    await interaction.response.edit_message(embed=embed, view=view_moi)
    view_moi.message = interaction.message
    view_cu.stop()


async def ve_bang_chinh(interaction: discord.Interaction, view_cu: OwnerView, log: str | None = None) -> None:
    p = await db.lay_nguoi_choi(interaction.user.id)
    view = MainView(p, interaction.user.id)
    await _chuyen_view(interaction, view_cu, embed_chinh(p, interaction.user, log), view)


# ===========================================================================
# BẢNG ĐIỀU KHIỂN CHÍNH
# ===========================================================================
class MainView(OwnerView):
    def __init__(self, player: dict, owner_id: int):
        super().__init__(owner_id)
        r = player["canh_gioi"]
        # Nút Đột Phá: xám + vô hiệu hóa nếu chưa đủ Linh lực (hoặc đã đăng đỉnh)
        du_dieu_kien = r < CANH_GIOI_TOI_DA and player["linh_luc"] >= CANH_GIOI[r]["yeu_cau"]
        self.dot_pha_btn.disabled = not du_dieu_kien
        self.dot_pha_btn.style = discord.ButtonStyle.success if du_dieu_kien else discord.ButtonStyle.secondary

    @ui.button(label="Tu Luyện", emoji="🧘", style=discord.ButtonStyle.primary, row=0)
    async def tu_luyen_btn(self, interaction: discord.Interaction, button: ui.Button):
        _, msg = await gl.tu_luyen(interaction.user.id)
        await ve_bang_chinh(interaction, self, msg)

    @ui.button(label="Đột Phá", emoji="⚡", style=discord.ButtonStyle.success, row=0)
    async def dot_pha_btn(self, interaction: discord.Interaction, button: ui.Button):
        _, msg = await gl.dot_pha(interaction.user.id)
        await ve_bang_chinh(interaction, self, msg)

    @ui.button(label="Làm Nhiệm Vụ", emoji="⚔️", style=discord.ButtonStyle.danger, row=0)
    async def nhiem_vu_btn(self, interaction: discord.Interaction, button: ui.Button):
        _, msg = await gl.lam_nhiem_vu(interaction.user.id)
        await ve_bang_chinh(interaction, self, msg)

    @ui.button(label="Túi Đồ", emoji="🎒", style=discord.ButtonStyle.secondary, row=1)
    async def tui_do_btn(self, interaction: discord.Interaction, button: ui.Button):
        p = await db.lay_nguoi_choi(interaction.user.id)
        view = BagView(p, interaction.user.id)
        await _chuyen_view(interaction, self, embed_tui(p, interaction.user), view)

    @ui.button(label="Chợ Đen", emoji="🕶️", style=discord.ButtonStyle.secondary, row=1)
    async def cho_den_btn(self, interaction: discord.Interaction, button: ui.Button):
        p = await db.lay_nguoi_choi(interaction.user.id)
        view = MarketView(p, interaction.user.id)
        await _chuyen_view(interaction, self, embed_cho_den(p, interaction.user), view)


# ===========================================================================
# TÚI ĐỒ
# ===========================================================================
class DungVatPhamSelect(ui.Select):
    def __init__(self, tui_do: dict):
        options = []
        for item_id, sl in tui_do.items():
            vp = VAT_PHAM.get(item_id)
            if vp and sl > 0:
                options.append(
                    discord.SelectOption(
                        label=f"{vp['ten']} x{sl}",
                        value=item_id,
                        description=vp["mo_ta"][:100],
                        emoji=vp["emoji"],
                    )
                )
        rong = not options
        if rong:  # Discord bắt buộc có ít nhất 1 option
            options = [discord.SelectOption(label="Túi đồ trống", value="none")]
        super().__init__(
            placeholder="Túi đồ trống" if rong else "🎒 Chọn vật phẩm để dùng...",
            options=options,
            disabled=rong,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction):
        _, msg = await gl.dung_vat_pham(interaction.user.id, self.values[0])
        await self.view.lam_moi(interaction, msg)


class BagView(OwnerView):
    def __init__(self, player: dict, owner_id: int):
        super().__init__(owner_id)
        self.add_item(DungVatPhamSelect(player["tui_do"]))

    async def lam_moi(self, interaction: discord.Interaction, log: str | None = None):
        p = await db.lay_nguoi_choi(interaction.user.id)
        view = BagView(p, interaction.user.id)
        await _chuyen_view(interaction, self, embed_tui(p, interaction.user, log), view)

    @ui.button(label="Quay lại", emoji="◀️", style=discord.ButtonStyle.secondary, row=1)
    async def quay_lai(self, interaction: discord.Interaction, button: ui.Button):
        await ve_bang_chinh(interaction, self)


# ===========================================================================
# CHỢ ĐEN
# ===========================================================================
class MuaSelect(ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label=f"Mua {vp['ten']} — {vp['gia_mua']:,} LT",
                value=item_id,
                description=vp["mo_ta"][:100],
                emoji=vp["emoji"],
            )
            for item_id, vp in VAT_PHAM.items()
        ]
        super().__init__(placeholder="🛒 Chọn đan dược để MUA (1 cái)", options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        _, msg = await gl.mua(interaction.user.id, self.values[0])
        await self.view.lam_moi(interaction, msg)


class BanSelect(ui.Select):
    def __init__(self, tui_do: dict):
        options = []
        for item_id, sl in tui_do.items():
            vp = VAT_PHAM.get(item_id)
            if vp and sl > 0:
                options.append(
                    discord.SelectOption(
                        label=f"Bán {vp['ten']} x{sl} — {vp['gia_ban']:,} LT/cái",
                        value=item_id,
                        description=vp["mo_ta"][:100],
                        emoji=vp["emoji"],
                    )
                )
        rong = not options
        if rong:
            options = [discord.SelectOption(label="Không có gì để bán", value="none")]
        super().__init__(
            placeholder="Túi đồ trống, không có gì để bán" if rong else "💰 Chọn vật phẩm để BÁN (1 cái)",
            options=options,
            disabled=rong,
            row=1,
        )

    async def callback(self, interaction: discord.Interaction):
        _, msg = await gl.ban(interaction.user.id, self.values[0])
        await self.view.lam_moi(interaction, msg)


class MarketView(OwnerView):
    def __init__(self, player: dict, owner_id: int):
        super().__init__(owner_id)
        self.add_item(MuaSelect())
        self.add_item(BanSelect(player["tui_do"]))

    async def lam_moi(self, interaction: discord.Interaction, log: str | None = None):
        p = await db.lay_nguoi_choi(interaction.user.id)
        view = MarketView(p, interaction.user.id)
        await _chuyen_view(interaction, self, embed_cho_den(p, interaction.user, log), view)

    @ui.button(label="Quay lại", emoji="◀️", style=discord.ButtonStyle.secondary, row=2)
    async def quay_lai(self, interaction: discord.Interaction, button: ui.Button):
        await ve_bang_chinh(interaction, self)
