"""Điểm khởi chạy bot Discord Tu Tiên."""

import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()  # đọc file .env khi chạy local (trên Render dùng Environment Variables)

import database as db  # noqa: E402
import views  # noqa: E402
from keep_alive import keep_alive  # noqa: E402

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")  # tùy chọn: điền để slash command hiện ngay lập tức


class TuTienBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=discord.Intents.default(),  # slash command không cần message_content
        )

    async def setup_hook(self) -> None:
        await db.ket_noi()
        if GUILD_ID:
            guild = discord.Object(id=int(GUILD_ID))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        else:
            await self.tree.sync()

    async def on_ready(self) -> None:
        print(f"☯️ Bot đã đăng nhập: {self.user} (ID: {self.user.id})")


bot = TuTienBot()


@bot.tree.command(name="game", description="Mở Bảng Điều Khiển Tu Tiên của bạn")
async def game(interaction: discord.Interaction):
    p = await db.lay_nguoi_choi(interaction.user.id)
    view = views.MainView(p, interaction.user.id)
    await interaction.response.send_message(
        embed=views.embed_chinh(p, interaction.user), view=view
    )
    view.message = await interaction.original_response()


if __name__ == "__main__":
    if not TOKEN:
        raise SystemExit("Thiếu DISCORD_TOKEN trong .env / biến môi trường!")
    keep_alive()  # mở web server nhỏ để Render/UptimeRobot ping
    bot.run(TOKEN)
