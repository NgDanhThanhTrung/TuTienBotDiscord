"""Điểm khởi chạy bot Discord Tu Tiên."""

import asyncio
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()  # đọc file .env khi chạy local (trên Render dùng Environment Variables)

import database as db  # noqa: E402
import lenh  # noqa: E402
from keep_alive import keep_alive  # noqa: E402

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = (os.getenv("GUILD_ID") or "").strip().strip("\"'")  # tùy chọn: điền để slash command hiện ngay
# Đặt SYNC_ON_START=1 trên Render CHỈ khi vừa thêm/sửa slash command, deploy xong nhớ xóa đi.
SYNC_ON_START = os.getenv("SYNC_ON_START") == "1"

# Thời gian chờ (giây) khi Discord/Cloudflare chặn IP, để không gây vòng lặp restart.
CHO_TOI_THIEU = 900    # 15 phút
CHO_TOI_DA = 3600      # 60 phút


async def dong_bo_lenh(bot: commands.Bot) -> tuple[int, str]:
    """Đồng bộ slash command lên Discord. Trả về (số lệnh, mô tả chế độ)."""
    if GUILD_ID:
        guild = discord.Object(id=int(GUILD_ID))
        bot.tree.copy_global_to(guild=guild)
        dong_bo = await bot.tree.sync(guild=guild)
        return len(dong_bo), f"server {GUILD_ID}"
    dong_bo = await bot.tree.sync()
    return len(dong_bo), "toàn cầu (chậm, có thể mất vài phút)"


class TuTienBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=discord.Intents.default(),  # slash command không cần message_content
        )

    async def setup_hook(self) -> None:
        await db.ket_noi()
        if SYNC_ON_START:
            n, che_do = await dong_bo_lenh(self)
            print(f"🔄 Đã đồng bộ {n} slash command • chế độ: {che_do}")

    async def on_ready(self) -> None:
        print(f"☯️ Bot đã đăng nhập: {self.user} (ID: {self.user.id})")
        print(f"🔧 GUILD_ID = {GUILD_ID or '(trống → sync toàn cầu)'}")


def tao_bot() -> TuTienBot:
    bot = TuTienBot()

    lenh.dang_ky(bot)  # đăng ký các slash command gõ tay (/start, /tuluyen, ...)

    @bot.command(name="sync")
    @commands.is_owner()
    async def sync(ctx: commands.Context):
        """Chủ bot gõ: @TênBot sync  -> đồng bộ slash command (chỉ khi cần)."""
        n, che_do = await dong_bo_lenh(bot)
        await ctx.reply(f"🔄 Đã đồng bộ {n} slash command • chế độ: {che_do}")

    @bot.command(name="xoaglobal")
    @commands.is_owner()
    async def xoaglobal(ctx: commands.Context):
        """Xóa lệnh toàn cầu cũ (dùng khi đã có GUILD_ID mà lệnh hiện 2 lần)."""
        if not GUILD_ID:
            await ctx.reply("Chưa đặt GUILD_ID nên không xóa, kẻo mất hết lệnh.")
            return
        await dong_bo_lenh(bot)                    # đảm bảo bản server đã đủ lệnh
        bot.tree.clear_commands(guild=None)        # xóa bản toàn cầu
        await bot.tree.sync()
        await ctx.reply("🧹 Đã xóa lệnh toàn cầu cũ, chỉ còn lệnh của server.")

    return bot


async def chay_bot() -> None:
    """Chạy bot; nếu bị chặn/rate limit thì chờ lâu rồi thử lại, KHÔNG thoát tiến trình."""
    cho = CHO_TOI_THIEU
    while True:
        bot = tao_bot()
        try:
            async with bot:
                await bot.start(TOKEN)
            return  # bot đóng bình thường
        except discord.LoginFailure:
            raise SystemExit("DISCORD_TOKEN sai hoặc đã bị reset!")
        except discord.HTTPException as e:
            # 429 / trang HTML của Cloudflare (lỗi 1015) -> IP đang bị chặn tạm thời
            print(f"⚠️ Discord từ chối kết nối (HTTP {e.status}). Chờ {cho // 60} phút rồi thử lại.")
        except Exception as e:  # noqa: BLE001 - lỗi mạng/Mongo tạm thời
            print(f"⚠️ Lỗi khi khởi động: {e!r}. Chờ {cho // 60} phút rồi thử lại.")
        await asyncio.sleep(cho)
        cho = min(cho * 2, CHO_TOI_DA)


if __name__ == "__main__":
    if not TOKEN:
        raise SystemExit("Thiếu DISCORD_TOKEN trong .env / biến môi trường!")
    keep_alive()  # mở web server nhỏ để Render/UptimeRobot ping
    asyncio.run(chay_bot())
