import asyncio
import discord
from discord.ext import commands
import time
import platform
import psutil
from database import db
from utils.helpers import format_time, create_info_embed, create_success_embed
from config import Config

class Utility(commands.Cog, name="🛠️ أدوات مساعدة"):
    """أوامر مساعدة وأدوات عامة"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.command(name='بينج', aliases=['ping', 'سرعة'])
    async def ping(self, ctx: commands.Context):
        """سرعة البوت"""
        websocket_latency = round(self.bot.latency * 1000)
        
        start = time.perf_counter()
        msg = await ctx.send("🏓 بحسب...")
        end = time.perf_counter()
        message_latency = round((end - start) * 1000)
        
        embed = discord.Embed(
            title="🏓 بينج!",
            color=Config.COLORS['info']
        )
        embed.add_field(name="🌐 WebSocket", value=f"`{websocket_latency}ms`", inline=True)
        embed.add_field(name="💬 الرسائل", value=f"`{message_latency}ms`", inline=True)
        embed.add_field(name="🖥️ السيرفر", value=f"`{psutil.Process().cpu_percent():.1f}%`", inline=True)
        
        await msg.edit(content=None, embed=embed)
    
    @commands.command(name='معلومات_البوت', aliases=['botinfo', 'بوت'])
    async def botinfo(self, ctx: commands.Context):
        """معلومات عن البوت"""
        uptime = int(time.time() - self.bot.launch_time.timestamp()) if hasattr(self.bot, 'launch_time') else 0
        
        embed = discord.Embed(
            title="🤖 معلومات البوت",
            description="البوت الذكي العربي المتقدم",
            color=Config.COLORS['primary']
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        
        embed.add_field(name="👤 الاسم", value=self.bot.user.name, inline=True)
        embed.add_field(name="🆔 المعرف", value=self.bot.user.id, inline=True)
        embed.add_field(name="📊 السيرفرات", value=f"{len(self.bot.guilds)} سيرفر", inline=True)
        embed.add_field(name="👥 الأعضاء", value=f"{sum(g.member_count for g in self.bot.guilds)} عضو", inline=True)
        embed.add_field(name="⏱️ وقت التشغيل", value=format_time(uptime), inline=True)
        embed.add_field(name="🐍 Python", value=platform.python_version(), inline=True)
        embed.add_field(name="🔗 Discord.py", value=discord.__version__, inline=True)
        embed.add_field(name="📦 الـ Cogs", value=str(len(self.bot.cogs)), inline=True)
        embed.add_field(name="⚡ الأوامر", value=str(len(self.bot.commands)), inline=True)
        
        embed.add_field(
            name="👑 المطور",
            value="<@!706940704032833546>" if not Config.OWNER_IDS else f"<@!{Config.OWNER_IDS[0]}>",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='معلوماتي', aliases=['userinfo', 'معلومة'])
    async def userinfo(self, ctx: commands.Context, member: discord.Member = None):
        """معلومات عن عضو"""
        member = member or ctx.author
        
        roles = [role.mention for role in member.roles if role != ctx.guild.default_role]
        roles_str = ', '.join(roles[:20]) if roles else "لا يوجد"
        if len(roles) > 20:
            roles_str += f" (+{len(roles) - 20} آخر)"
        
        from utils.helpers import get_status_emoji, get_activity_text
        
        embed = discord.Embed(
            title=f"👤 معلومات {member.display_name}",
            color=member.color if member.color != discord.Color.default() else Config.COLORS['info']
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        
        embed.add_field(name="🆔 المعرف", value=member.id, inline=True)
        embed.add_field(name="🏷️ الاسم", value=f"{member.name}#{member.discriminator}", inline=True)
        embed.add_field(name="🤖 بوت؟", value="نعم" if member.bot else "لا", inline=True)
        
        embed.add_field(name="📅 تاريخ الانضمام", value=f"<t:{int(member.joined_at.timestamp())}:R>", inline=True)
        embed.add_field(name="📅 تاريخ التسجيل", value=f"<t:{int(member.created_at.timestamp())}:R>", inline=True)
        embed.add_field(name="🎨 أعلى رتبة", value=member.top_role.mention, inline=True)
        
        embed.add_field(name="📜 الرتب", value=roles_str, inline=False)
        
        if member.premium_since:
            embed.add_field(name="💎 نيترو", value=f"منذ <t:{int(member.premium_since.timestamp())}:R>", inline=True)
        
        embed.add_field(name="📸 الصورة", value=f"[رابط الصورة]({member.display_avatar.url})", inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='السيرفر', aliases=['serverinfo', 'سيرفر'])
    async def serverinfo(self, ctx: commands.Context):
        """معلومات السيرفر"""
        guild = ctx.guild
        
        # إحصائيات الأعضاء
        total_members = guild.member_count
        bots = sum(1 for m in guild.members if m.bot)
        humans = total_members - bots
        
        online = sum(1 for m in guild.members if m.status == discord.Status.online and not m.bot)
        idle = sum(1 for m in guild.members if m.status == discord.Status.idle and not m.bot)
        dnd = sum(1 for m in guild.members if m.status == discord.Status.dnd and not m.bot)
        offline = sum(1 for m in guild.members if m.status == discord.Status.offline and not m.bot)
        
        # إحصائيات القنوات
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        
        # إحصائيات أخرى
        roles_count = len(guild.roles) - 1  # بدون @everyone
        emojis_count = len(guild.emojis)
        boost_level = guild.premium_tier
        boosters = guild.premium_subscription_count
        
        embed = discord.Embed(
            title=f"📊 معلومات {guild.name}",
            color=Config.COLORS['info']
        )
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        if guild.banner:
            embed.set_image(url=guild.banner.url)
        
        embed.add_field(name="👑 المالك", value=guild.owner.mention, inline=True)
        embed.add_field(name="🆔 المعرف", value=guild.id, inline=True)
        embed.add_field(name="📅 تاريخ الإنشاء", value=f"<t:{int(guild.created_at.timestamp())}:R>", inline=True)
        
        embed.add_field(
            name=f"👥 الأعضاء ({total_members})",
            value=(
                f"👤 بشر: **{humans}**\n"
                f"🤖 بوتات: **{bots}**\n"
                f"🟢 متصل: **{online}**\n"
                f"🟡 مشغول: **{idle}**\n"
                f"🔴 مش إزعاج: **{dnd}**\n"
                f"⚫ غير متصل: **{offline}**"
            ),
            inline=True
        )
        
        embed.add_field(
            name=f"📝 القنوات ({text_channels + voice_channels})",
            value=(
                f"💬 نصية: **{text_channels}**\n"
                f"🎤 صوتية: **{voice_channels}**\n"
                f"📂 تصنيفات: **{categories}**"
            ),
            inline=True
        )
        
        embed.add_field(
            name="✨ أخرى",
            value=(
                f"🎭 رتب: **{roles_count}**\n"
                f"😀 إيموجي: **{emojis_count}**\n"
                f"🚀 مستوى البوست: **{boost_level}**\n"
                f"💎 عدد البوستات: **{boosters}**"
            ),
            inline=True
        )
        
        if guild.description:
            embed.add_field(name="📝 الوصف", value=guild.description[:1024], inline=False)
        
        features = []
        feature_map = {
            'VANITY_URL': '🔗 رابط مخصص',
            'VERIFIED': '✅ موثق',
            'PARTNERED': '🤝 شريك',
            'DISCOVERABLE': '🔍 قابل للاكتشاف',
            'COMMUNITY': '👥 مجتمع',
            'NEWS': '📢 قنوات أخبار',
            'BANNER': '🖼️ بانر',
            'INVITE_SPLASH': '🎨 صورة دعوة',
            'VIP_REGIONS': '🌟 مناطق VIP',
            'VANITY_URL': '🔗 رابط مخصص',
        }
        for feature in guild.features:
            if feature in feature_map:
                features.append(feature_map[feature])
        
        if features:
            embed.add_field(name="✨ المميزات", value='\n'.join(features[:10]), inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='الافатар', aliases=['avatar', 'صورة'])
    async def avatar(self, ctx: commands.Context, member: discord.Member = None):
        """عرض صورة البروفايل"""
        member = member or ctx.author
        
        embed = discord.Embed(
            title=f"🖼️ صورة {member.display_name}",
            color=member.color if member.color != discord.Color.default() else Config.COLORS['info']
        )
        embed.set_image(url=member.display_avatar.url)
        
        # روابط الأحجام المختلفة
        links = []
        for size in [16, 32, 64, 128, 256, 512, 1024, 2048, 4096]:
            links.append(f"[{size}]({member.display_avatar.replace(size=size)})")
        
        embed.add_field(
            name="📥 تحميل بالأحجام",
            value=" | ".join(links),
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='قول', aliases=['say', 'اكتب'])
    @commands.has_permissions(manage_messages=True)
    async def say(self, ctx: commands.Context, channel: discord.TextChannel = None, *, message: str):
        """البوت يكتب رسالة"""
        channel = channel or ctx.channel
        
        if not channel.permissions_for(ctx.guild.me).send_messages:
            await ctx.send("❌ مفيش صلاحية الإرسال في القناة دي!")
            return
        
        try:
            await ctx.message.delete()
        except:
            pass
        
        await channel.send(message)
    
    @commands.command(name='مسح', aliases=['clear', 'حذف'])
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def clear(self, ctx: commands.Context, amount: int = 10, member: discord.Member = None):
        """مسح الرسائل"""
        if amount < 1 or amount > 1000:
            await ctx.send("❌ العدد لازم يكون بين 1 و 1000")
            return
        
        def check(m):
            if member:
                return m.author.id == member.id
            return True
        
        deleted = await ctx.channel.purge(limit=amount + 1, check=check)
        
        msg = await ctx.send(
            f"✅ تم مسح **{len(deleted) - 1}** رسالة!" + 
            (f" من {member.mention}" if member else ""),
            delete_after=5
        )


    @commands.command(name='مسح_الكل', aliases=['clearall', 'مسح_القناة', 'clearallchannel'])
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def clear_all(self, ctx: commands.Context):
        """مسح كل الرسائل في القناة"""
        
        # تأكيد قبل المسح
        from utils.views import ConfirmView
        view = ConfirmView(ctx.author.id, timeout=30)
        
        warning_embed = discord.Embed(
            title="⚠️ تحذير خطير!",
            description=(
                f"انت على وشك مسح **كل الرسائل** في {ctx.channel.mention}\n\n"
                f"⚠️ العملية دي **مش هتترد**!\n\n"
                f"متأكد إنك عايز تكمل؟"
            ),
            color=Config.COLORS['warning']
        )
        
        msg = await ctx.send(embed=warning_embed, view=view)
        await view.wait()
        
        if not view.value:
            try:
                await msg.edit(content="❌ تم إلغاء العملية", embed=None, view=None)
            except:
                pass
            return
        
        # مسح رسالة التأكيد قبل ما نبدأ
        try:
            await msg.delete()
        except:
            pass
        
        # حساب عدد الرسائل
        status_msg = await ctx.send("🔄 جاري حساب الرسائل...")
        
        total_count = 0
        async for _ in ctx.channel.history(limit=None):
            total_count += 1
        
        # مسح الرسائل
        deleted_count = 0
        try:
            while True:
                deleted = await ctx.channel.purge(limit=1000, bulk=True)
                deleted_count += len(deleted)
                
                # تحديث رسالة التقدم
                try:
                    await status_msg.edit(content=f"🗑️ جاري المسح... تم مسح **{deleted_count}** رسالة")
                except:
                    pass
                
                if len(deleted) < 1000:
                    break
                
                await asyncio.sleep(1)
        
        except discord.HTTPException as e:
            if e.code == 50034:
                try:
                    await status_msg.edit(content="⚠️ فيه رسائل قديمة، جاري مسحها واحدة واحدة...")
                except:
                    pass
                
                async for message in ctx.channel.history(limit=None):
                    try:
                        await message.delete()
                        deleted_count += 1
                    except:
                        pass
        
        except Exception as e:
            try:
                await status_msg.edit(content=f"❌ حصل خطأ: {str(e)[:100]}")
            except:
                await ctx.send(f"❌ حصل خطأ: {str(e)[:100]}")
            return
        
        # رسالة النجاح
        try:
            await status_msg.edit(content=f"✅ تم مسح **{deleted_count}** رسالة من القناة!")
        except:
            await ctx.send(f"✅ تم مسح **{deleted_count}** رسالة من القناة!")
        
        # مسح رسالة النجاح بعد 5 ثواني
        await asyncio.sleep(5)
        try:
            await status_msg.delete()
        except:
            pass
async def setup(bot: commands.Bot):
    await bot.add_cog(Utility(bot))