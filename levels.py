import discord
from discord.ext import commands
import random
import time
from database import db
from utils.helpers import get_xp_for_level, create_progress_bar, format_number
from config import Config
from utils.views import PaginationView

class Levels(commands.Cog, name="📊 المستويات"):
    """نظام المستويات المتقدم"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """إضافة XP للرسائل"""
        if message.author.bot or not message.guild:
            return
        
        # فحص إعدادات السيرفر
        settings = await db.get_guild_settings(message.guild.id)
        if not settings.get('leveling_enabled', 1):
            return
        
        # Cooldown
        data = await db.get_user_level(message.author.id)
        current_time = int(time.time())
        
        if current_time - data['last_xp'] < Config.LEVELS['cooldown']:
            return
        
        # إضافة XP
        xp_gain = random.randint(Config.LEVELS['xp_min'], Config.LEVELS['xp_max'])
        old_level, new_level = await db.add_xp(message.author.id, xp_gain)
        
        # إشعار المستوى الجديد
        if new_level > old_level:
            embed = discord.Embed(
                title="🎊 ترقية المستوى!",
                description=f"{message.author.mention} وصل للمستوى **{new_level}** 🎉",
                color=Config.COLORS['primary']
            )
            
            # مكافأة مالية
            reward = new_level * 100
            from database import db as economy_db
            await economy_db.update_balance(message.author.id, reward)
            
            embed.add_field(name="💰 المكافأة", value=f"+{reward:,} جنيه")
            
            try:
                await message.channel.send(embed=embed, delete_after=10)
            except:
                pass
    
    @commands.command(name='رتبتي', aliases=['rank', 'مستواي', 'level'])
    async def rank(self, ctx: commands.Context, member: discord.Member = None):
        """عرض رتبتك"""
        member = member or ctx.author
        
        if member.bot:
            await ctx.send("❌ البوتات مفيش ليها مستويات!")
            return
        
        data = await db.get_user_level(member.id)
        required_xp = get_xp_for_level(data['level'])
        progress = (data['xp'] / required_xp) * 100 if required_xp > 0 else 0
        
        # حساب الترتيب
        rows = await db.fetch(
            'SELECT user_id FROM levels ORDER BY level DESC, xp DESC'
        )
        user_rank = next((i+1 for i, row in enumerate(rows) if row[0] == member.id), None)
        
        embed = discord.Embed(
            title=f"📊 بطاقة رتبة {member.display_name}",
            color=member.color if member.color != discord.Color.default() else Config.COLORS['info']
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        
        embed.add_field(name="📈 المستوى", value=f"**{data['level']}**", inline=True)
        embed.add_field(name="🏆 الترتيب", value=f"**#{user_rank or '?'}**", inline=True)
        embed.add_field(name="💬 الرسائل", value=f"**{format_number(data['total_messages'])}**", inline=True)
        
        embed.add_field(
            name=f"⭐ XP ({data['xp']:,}/{required_xp:,})",
            value=f"`{create_progress_bar(data['xp'], required_xp)}` **{progress:.1f}%**",
            inline=False
        )
        
        # المستوى التالي
        next_level_xp = get_xp_for_level(data['level'] + 1)
        remaining_xp = next_level_xp - data['xp']
        embed.add_field(
            name="🎯 المستوى التالي",
            value=f"محتاج **{remaining_xp:,}** XP للمستوى {data['level'] + 1}",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='ترتيب_المستويات', aliases=['أوائل_المستويات', 'levels_top', 'top_xp'])
    async def top(self, ctx: commands.Context):
        """لوحة المتصدرين في المستويات"""
        rows = await db.get_leaderboard(100)
        
        if not rows:
            await ctx.send("❌ مفيش بيانات!")
            return
        
        pages = []
        medals = ['🥇', '🥈', '🥉']
        
        for i in range(0, len(rows), 10):
            chunk = rows[i:i+10]
            embed = discord.Embed(
                title="🏆 أوائل الأعضاء في المستويات",
                color=Config.COLORS['primary']
            )
            
            for j, row in enumerate(chunk):
                user_id, level, xp, messages = row
                rank = i + j + 1
                medal = medals[rank-1] if rank <= 3 else f"#{rank}"
                
                try:
                    user = await self.bot.fetch_user(user_id)
                    name = user.name
                except:
                    name = f"Unknown ({user_id})"
                
                embed.add_field(
                    name=f"{medal} {name}",
                    value=f"📈 المستوى: **{level}** | ⭐ XP: **{xp:,}** | 💬 الرسائل: **{messages:,}**",
                    inline=False
                )
            
            pages.append(embed)
        
        if len(pages) == 1:
            await ctx.send(embed=pages[0])
        else:
            view = PaginationView(pages, ctx.author.id)
            msg = await ctx.send(embed=pages[0], view=view)
            view.message = msg

async def setup(bot: commands.Bot):
    await bot.add_cog(Levels(bot))