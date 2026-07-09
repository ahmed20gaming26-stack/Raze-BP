import discord
from discord.ext import commands, tasks
import time
from database import db
from config import Config
from utils.helpers import format_time, parse_time, get_timestamp

class Reminders(commands.Cog, name="⏰ التذكيرات"):
    """نظام التذكيرات"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.check_reminders.start()
    
    def cog_unload(self):
        self.check_reminders.cancel()
    
    @tasks.loop(seconds=30)
    async def check_reminders(self):
        """فحص التذكيرات"""
        current_time = int(time.time())
        
        rows = await db.fetch(
            'SELECT * FROM reminders WHERE remind_time <= ?',
            (current_time,)
        )
        
        for row in rows:
            id_, user_id, channel_id, message, remind_time, created_at = row
            
            try:
                user = await self.bot.fetch_user(user_id)
                channel = self.bot.get_channel(channel_id)
                
                if channel:
                    embed = discord.Embed(
                        title="⏰ تذكير!",
                        description=f"**📝 الرسالة:** {message}\n\n**⏰ تم التذكير في:** {get_timestamp(current_time)}",
                        color=Config.COLORS['warning']
                    )
                    
                    await channel.send(f"⏰ {user.mention}", embed=embed)
                
                # محاولة إرسال DM
                try:
                    await user.send(f"⏰ **تذكير:** {message}")
                except:
                    pass
                
            except Exception as e:
                print(f"خطأ في التذكير: {e}")
            
            await db.execute('DELETE FROM reminders WHERE id = ?', (id_,))
    
    @check_reminders.before_loop
    async def before_check_reminders(self):
        await self.bot.wait_until_ready()
    
    @commands.command(name='ذكرني', aliases=['remind', 'تذكير'])
    async def remind(self, ctx: commands.Context, time_str: str, *, message: str):
        """إنشاء تذكير"""
        seconds = parse_time(time_str)
        if not seconds or seconds <= 0:
            await ctx.send("❌ الوقت غلط! مثال: `10m`, `1h`, `1d`")
            return
        
        remind_time = int(time.time()) + seconds
        
        await db.execute(
            'INSERT INTO reminders (user_id, channel_id, message, remind_time, created_at) VALUES (?, ?, ?, ?, ?)',
            (ctx.author.id, ctx.channel.id, message, remind_time, int(time.time()))
        )
        
        embed = discord.Embed(
            title="⏰ تم إنشاء تذكير!",
            description=(
                f"**📝 الرسالة:** {message}\n"
                f"**⏰ التذكير في:** {get_timestamp(remind_time, 'R')}\n"
                f"**📅 الوقت:** {get_timestamp(remind_time, 'f')}"
            ),
            color=Config.COLORS['success']
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='تذكيراتي', aliases=['myreminders'])
    async def my_reminders(self, ctx: commands.Context):
        """عرض تذكيراتك"""
        rows = await db.fetch(
            'SELECT * FROM reminders WHERE user_id = ? ORDER BY remind_time ASC',
            (ctx.author.id,)
        )
        
        if not rows:
            await ctx.send("❌ مفيش عندك تذكيرات!")
            return
        
        embed = discord.Embed(
            title="⏰ تذكيراتك",
            color=Config.COLORS['info']
        )
        
        for i, row in enumerate(rows[:25], 1):
            id_, user_id, channel_id, message, remind_time, created_at = row
            
            embed.add_field(
                name=f"#{i} - {get_timestamp(remind_time, 'R')}",
                value=f"📝 {message[:100]}",
                inline=False
            )
        
        await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Reminders(bot))