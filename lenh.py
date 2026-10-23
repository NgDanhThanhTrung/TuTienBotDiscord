"""Slash command gõ tay: dùng song song với nút bấm trong bảng điều khiển.

Mỗi lệnh gọi đúng hàm trong game_logic mà nút bấm cũng gọi, rồi gửi lại bảng
điều khiển (vẫn có đủ nút) để người chơi có thể tiếp tục bấm hoặc gõ lệnh.
"""

import discord
from discord import app_commands

import database as db
import game_logic as gl
import views
from game_data import VAT_PHAM

# Danh sách vật phẩm hiện ra khi gõ /dung, /mua, /ban
VAT_PHAM_CHOICES = [
    app_commands.Choice(name=vp["ten"], value=item_id) for item_id, vp in VAT_PHAM.items()
]


async def _gui_bang_chinh(interaction: discord.Interaction, log: str | None = None, **kw):
    p = await db.lay_nguoi_choi(interaction.user.id)
    view = views.MainView(p, interaction.user.id)
    await interaction.response.send_message(
        embed=views.embed_chinh(p, interaction.user, log), view=view, **kw
    )
    view.message = await interaction.original_response()


async def _da_start(interaction: discord.Interaction) -> bool:
    if await db.da_co_nguoi_choi(interaction.user.id):
        return True
    await interaction.response.send_message(
        "Bạn chưa bắt đầu tu tiên. Hãy gõ `/start` trước nhé!", ephemeral=True
    )
    return False


def dang_ky(bot) -> None:
    tree = bot.tree

    @tree.command(name="start", description="Bắt đầu con đường tu tiên (tạo nhân vật)")
    async def start(interaction: discord.Interaction):
        da_co = await db.da_co_nguoi_choi(interaction.user.id)
        await db.lay_nguoi_choi(interaction.user.id)  # chưa có thì tạo mới
        loi_chao = (
            "📖 Bạn đã có hồ sơ tu tiên, đây là bảng điều khiển của bạn."
            if da_co
            else "🌟 Chào mừng đạo hữu bước vào con đường tu tiên! Hồ sơ đã được tạo."
        )
        await _gui_bang_chinh(interaction, loi_chao)

    @tree.command(name="game", description="Mở Bảng Điều Khiển Tu Tiên của bạn")
    async def game(interaction: discord.Interaction):
        if await _da_start(interaction):
            await _gui_bang_chinh(interaction)

    @tree.command(name="tuluyen", description="Tu luyện để tăng Linh lực")
    async def tuluyen(interaction: discord.Interaction):
        if await _da_start(interaction):
            _, msg = await gl.tu_luyen(interaction.user.id)
            await _gui_bang_chinh(interaction, msg)

    @tree.command(name="dotpha", description="Đột phá lên cảnh giới mới")
    async def dotpha(interaction: discord.Interaction):
        if await _da_start(interaction):
            _, msg = await gl.dot_pha(interaction.user.id)
            await _gui_bang_chinh(interaction, msg)

    @tree.command(name="nhiemvu", description="Làm nhiệm vụ kiếm Linh lực và Linh thạch")
    async def nhiemvu(interaction: discord.Interaction):
        if await _da_start(interaction):
            _, msg = await gl.lam_nhiem_vu(interaction.user.id)
            await _gui_bang_chinh(interaction, msg)

    @tree.command(name="tui", description="Xem túi đồ của bạn")
    async def tui(interaction: discord.Interaction):
        if not await _da_start(interaction):
            return
        p = await db.lay_nguoi_choi(interaction.user.id)
        view = views.BagView(p, interaction.user.id)
        await interaction.response.send_message(embed=views.embed_tui(p, interaction.user), view=view)
        view.message = await interaction.original_response()

    @tree.command(name="cho", description="Ghé Chợ Đen mua bán đan dược")
    async def cho(interaction: discord.Interaction):
        if not await _da_start(interaction):
            return
        p = await db.lay_nguoi_choi(interaction.user.id)
        view = views.MarketView(p, interaction.user.id)
        await interaction.response.send_message(embed=views.embed_cho_den(p, interaction.user), view=view)
        view.message = await interaction.original_response()

    @tree.command(name="dung", description="Dùng một vật phẩm trong túi đồ")
    @app_commands.describe(vat_pham="Vật phẩm muốn dùng")
    @app_commands.choices(vat_pham=VAT_PHAM_CHOICES)
    async def dung(interaction: discord.Interaction, vat_pham: app_commands.Choice[str]):
        if await _da_start(interaction):
            _, msg = await gl.dung_vat_pham(interaction.user.id, vat_pham.value)
            await _gui_bang_chinh(interaction, msg)

    @tree.command(name="mua", description="Mua 1 vật phẩm ở Chợ Đen")
    @app_commands.describe(vat_pham="Vật phẩm muốn mua")
    @app_commands.choices(vat_pham=VAT_PHAM_CHOICES)
    async def mua(interaction: discord.Interaction, vat_pham: app_commands.Choice[str]):
        if await _da_start(interaction):
            _, msg = await gl.mua(interaction.user.id, vat_pham.value)
            await _gui_bang_chinh(interaction, msg)

    @tree.command(name="ban", description="Bán 1 vật phẩm ở Chợ Đen")
    @app_commands.describe(vat_pham="Vật phẩm muốn bán")
    @app_commands.choices(vat_pham=VAT_PHAM_CHOICES)
    async def ban(interaction: discord.Interaction, vat_pham: app_commands.Choice[str]):
        if await _da_start(interaction):
            _, msg = await gl.ban(interaction.user.id, vat_pham.value)
            await _gui_bang_chinh(interaction, msg)
