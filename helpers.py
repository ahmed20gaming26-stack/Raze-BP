import discord
import random
import time
import datetime
from typing import Optional
from config import Config

def format_time(seconds: int) -> str:
    """تنسيق الوقت بالعربي"""
    if seconds < 0:
        return "الآن"
    
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    parts = []
    if days > 0: parts.append(f"{days} يوم")
    if hours > 0: parts.append(f"{hours} ساعة")
    if minutes > 0: parts.append(f"{minutes} دقيقة")
    if seconds > 0: parts.append(f"{seconds} ثانية")
    
    return " و ".join(parts) if parts else "لحظة"

def format_number(number: int) -> str:
    """تنسيق الأرقام الكبيرة"""
    if number >= 1_000_000_000:
        return f"{number / 1_000_000_000:.1f}B"
    if number >= 1_000_000:
        return f"{number / 1_000_000:.1f}M"
    if number >= 1_000:
        return f"{number / 1_000:.1f}K"
    return str(number)

def create_progress_bar(current: int, total: int, length: int = 20) -> str:
    """إنشاء شريط تقدم"""
    if total <= 0:
        return "░" * length
    progress = int((current / total) * length)
    return "█" * min(progress, length) + "░" * (length - min(progress, length))

def get_xp_for_level(level: int) -> int:
    """حساب XP المطلوب للمستوى"""
    return 5 * (level ** 2) + 50 * level + 100

def create_error_embed(title: str, description: str) -> discord.Embed:
    """إنشاء Embed خطأ"""
    embed = discord.Embed(
        title=f"❌ {title}",
        description=description,
        color=Config.COLORS['error']
    )
    return embed

def create_success_embed(title: str, description: str) -> discord.Embed:
    """إنشاء Embed نجاح"""
    embed = discord.Embed(
        title=f"✅ {title}",
        description=description,
        color=Config.COLORS['success']
    )
    return embed

def create_info_embed(title: str, description: str) -> discord.Embed:
    """إنشاء Embed معلومات"""
    embed = discord.Embed(
        title=f"ℹ️ {title}",
        description=description,
        color=Config.COLORS['info']
    )
    return embed

def get_random_color() -> discord.Color:
    """لون عشوائي"""
    return discord.Color(random.randint(0, 0xFFFFFF))

def truncate(text: str, max_length: int = 100) -> str:
    """اختصار النص"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def get_timestamp(timestamp: int, style: str = 'f') -> str:
    """إنشاء Discord timestamp"""
    return f"<t:{timestamp}:{style}>"

def parse_time(time_str: str) -> Optional[int]:
    """تحويل نص الوقت لثواني (مثل: 1d, 2h, 30m, 45s)"""
    time_units = {
        's': 1, 'sec': 1, 'ثانية': 1,
        'm': 60, 'min': 60, 'دقيقة': 60,
        'h': 3600, 'hour': 3600, 'ساعة': 3600,
        'd': 86400, 'day': 86400, 'يوم': 86400,
        'w': 604800, 'week': 604800, 'أسبوع': 604800,
    }
    
    import re
    match = re.match(r'^(\d+)\s*([a-zA-Zء-ي]+)$', time_str.strip())
    if not match:
        return None
    
    value, unit = match.groups()
    value = int(value)
    
    if unit in time_units:
        return value * time_units[unit]
    return None

async def confirm_action(ctx, message: str, timeout: int = 30) -> bool:
    """تأكيد إجراء بزرار"""
    class ConfirmView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=timeout)
            self.value = None
        
        @discord.ui.button(label="✅ تأكيد", style=discord.ButtonStyle.success)
        async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
            self.value = True
            self.stop()
        
        @discord.ui.button(label="❌ إلغاء", style=discord.ButtonStyle.danger)
        async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
            self.value = False
            self.stop()
    
    view = ConfirmView()
    embed = create_info_embed("⚠️ تأكيد", message)
    msg = await ctx.send(embed=embed, view=view)
    await view.wait()
    
    try:
        await msg.delete()
    except:
        pass
    
    return view.value or False

def get_status_emoji(status: discord.Status) -> str:
    """إيموجي حالة العضو"""
    status_map = {
        discord.Status.online: "🟢",
        discord.Status.idle: "🟡",
        discord.Status.dnd: "🔴",
        discord.Status.offline: "⚫",
    }
    return status_map.get(status, "⚪")

def get_activity_text(activity) -> str:
    """نص نشاط العضو"""
    if not activity:
        return "لا يوجد"
    
    if isinstance(activity, discord.Game):
        return f"🎮 يلعب {activity.name}"
    elif isinstance(activity, discord.Streaming):
        return f"📺 يبث {activity.name}"
    elif isinstance(activity, discord.Spotify):
        return f"🎵 يستمع إلى {activity.title} - {activity.artist}"
    elif isinstance(activity, discord.Activity):
        if activity.type == discord.ActivityType.playing:
            return f"🎮 يلعب {activity.name}"
        elif activity.type == discord.ActivityType.streaming:
            return f"📺 يبث {activity.name}"
        elif activity.type == discord.ActivityType.listening:
            return f"🎧 يستمع إلى {activity.name}"
        elif activity.type == discord.ActivityType.watching:
            return f"👀 يشاهد {activity.name}"
        elif activity.type == discord.ActivityType.competing:
            return f"🏆 يتنافس في {activity.name}"
    
    return str(activity)