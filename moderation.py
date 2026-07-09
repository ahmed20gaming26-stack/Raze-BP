import discord
from discord.ext import commands
import time
from database import db
from utils.helpers import format_time, create_success_embed, create_error_embed, confirm_action
from config import Config

class Moderation(commands.Cog, name="🛡️ الإدارة"):
    """أوامر الإدارة والإشراف"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    async def log_action(self, guild: discord.Guild, action: str, user: discord.Member, target: discord.Member = None, reason: str = None, **kwargs):
        """تسجيل الإجراء في السجلات"""
        settings = await db.get_guild_settings(guild.id)
        logs_channel_id = settings.get('logs_channel')
        
        if not logs_channel_id:
            return
        
        logs_channel = guild.get_channel(logs_channel_id)
        if not logs_channel:
            return
        
        embed = discord.Embed(
            title=f"🛡️ {action}",
            color=Config.COLORS['warning']
        )
        
        if target:
            embed.add_field(name="👤 المستخدم", value=f"{target.mention} ({target.id})", inline=True)
        embed.add_field(name="👮 بواسطة", value=f"{user.mention}", inline=True)
        
        if reason:
            embed.add_field(name="📝 السبب", value=reason, inline=False)
        
        for key, value in kwargs.items():
            embed.add_field(name=key, value=str(value), inline=True)
        
        embed.set_footer(text=f"الوقت: {int(time.time())}")
        
        try:
            await logs_channel.send(embed=embed)
        except:
            pass
        
        # حفظ في قاعدة البيانات
        await db.execute(
            'INSERT INTO logs (guild_id, event_type, user_id, target_id, details, timestamp) VALUES (?, ?, ?, ?, ?, ?)',
            (guild.id, action, user.id, target.id if target else None, str(kwargs), int(time.time()))
        )
    
    @commands.command(name='كتم', aliases=['mute', 'تايم'])
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    async def timeout(self, ctx: commands.Context, member: discord.Member, duration: str = '10m', *, reason: str = "مفيش سبب"):
        """كتم عضو"""
        from utils.helpers import parse_time
        
        seconds = parse_time(duration)
        if not seconds or seconds <= 0:
            await ctx.send("❌ الوقت غلط! مثال: `10m`, `1h`, `1d`")
            return
        
        if seconds > 2419200:  # 28 يوم
            await ctx.send("❌ أقصى مدة هي 28 يوم!")
            return
        
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send("❌ مش ممكن تكتم شخص رتبته أعلى أو زي رتبتك!")
            return
        
        try:
            await member.timeout(duration=duration, reason=reason)
        except:
            import datetime
            await member.timeout(datetime.timedelta(seconds=seconds), reason=reason)
        
        embed = create_success_embed(
            "🔇 تم الكتم!",
            f"{member.mention} اتكتم لمدة **{format_time(seconds)}**"
        )
        embed.add_field(name="👮 بواسطة", value=ctx.author.mention, inline=True)
        embed.add_field(name="📝 السبب", value=reason, inline=True)
        
        await ctx.send(embed=embed)
        await self.log_action(ctx.guild, "كتم", ctx.author, member, reason, المدة=format_time(seconds))
        
        # محاولة إرسال رسالة للعضو
        try:
            dm_embed = discord.Embed(
                title="🔇 تم كتمك",
                description=f"تم كتمك في **{ctx.guild.name}**\n**السبب:** {reason}\n**المدة:** {format_time(seconds)}",
                color=Config.COLORS['error']
            )
            await member.send(embed=dm_embed)
        except:
            pass
    
    @commands.command(name='فك_كتم', aliases=['unmute', 'فك_تايم'])
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    async def remove_timeout(self, ctx: commands.Context, member: discord.Member):
        """فك الكتم"""
        try:
            await member.timeout(None)
            embed = create_success_embed("🔊 تم فك الكتم!", f"{member.mention} يقدر يتكلم تاني")
            await ctx.send(embed=embed)
            await self.log_action(ctx.guild, "فك كتم", ctx.author, member)
        except Exception as e:
            await ctx.send(f"❌ خطأ: {str(e)}")
    
    @commands.command(name='طرد', aliases=['kick'])
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick(self, ctx: commands.Context, member: discord.Member, *, reason: str = "مفيش سبب"):
        """طرد عضو"""
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send("❌ مش ممكن تطرد شخص رتبته أعلى أو زي رتبتك!")
            return
        
        if not await confirm_action(ctx, f"متأكد إنك عايز تطرد {member.mention}؟"):
            await ctx.send("❌ تم الإلغاء")
            return
        
        try:
            # محاولة إرسال رسالة
            try:
                dm_embed = discord.Embed(
                    title="👢 تم طردك",
                    description=f"تم طردك من **{ctx.guild.name}**\n**السبب:** {reason}",
                    color=Config.COLORS['error']
                )
                await member.send(embed=dm_embed)
            except:
                pass
            
            await member.kick(reason=f"{ctx.author}: {reason}")
            
            embed = create_success_embed("👢 تم الطرد!", f"{member.mention} اتطرد من السيرفر")
            embed.add_field(name="👮 بواسطة", value=ctx.author.mention, inline=True)
            embed.add_field(name="📝 السبب", value=reason, inline=True)
            
            await ctx.send(embed=embed)
            await self.log_action(ctx.guild, "طرد", ctx.author, member, reason)
        except Exception as e:
            await ctx.send(f"❌ خطأ: {str(e)}")
    
    @commands.command(name='حظر', aliases=['ban'])
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban(self, ctx: commands.Context, member: discord.Member, *, reason: str = "مفيش سبب"):
        """حظر عضو"""
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send("❌ مش ممكن تحظر شخص رتبته أعلى أو زي رتبتك!")
            return
        
        if not await confirm_action(ctx, f"متأكد إنك عايز تحظر {member.mention} نهائيًا؟"):
            await ctx.send("❌ تم الإلغاء")
            return
        
        try:
            # محاولة إرسال رسالة
            try:
                dm_embed = discord.Embed(
                    title="🔨 تم حظرك",
                    description=f"تم حظرك من **{ctx.guild.name}**\n**السبب:** {reason}",
                    color=Config.COLORS['error']
                )
                await member.send(embed=dm_embed)
            except:
                pass
            
            await member.ban(reason=f"{ctx.author}: {reason}")
            
            embed = create_success_embed("🔨 تم الحظر!", f"{member.mention} اتحظر من السيرفر")
            embed.add_field(name="👮 بواسطة", value=ctx.author.mention, inline=True)
            embed.add_field(name="📝 السبب", value=reason, inline=True)
            
            await ctx.send(embed=embed)
            await self.log_action(ctx.guild, "حظر", ctx.author, member, reason)
        except Exception as e:
            await ctx.send(f"❌ خطأ: {str(e)}")
    
    @commands.command(name='فك_حظر', aliases=['unban'])
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def unban(self, ctx: commands.Context, user_id: int):
        """فك حظر عضو"""
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user)
            
            embed = create_success_embed("✅ تم فك الحظر!", f"{user.mention} اتفك حظره")
            await ctx.send(embed=embed)
            await self.log_action(ctx.guild, "فك حظر", ctx.author, user)
        except discord.NotFound:
            await ctx.send("❌ المستخدم ده مش محظور أو مش موجود!")
        except Exception as e:
            await ctx.send(f"❌ خطأ: {str(e)}")
    
    @commands.command(name='تحذير', aliases=['warn'])
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx: commands.Context, member: discord.Member, *, reason: str = "مفيش سبب"):
        """تحذير عضو"""
        if member.bot:
            await ctx.send("❌ مش ممكن تحذر بوت!")
            return
        
        warn_id = await db.add_warn(ctx.guild.id, member.id, ctx.author.id, reason)
        warns = await db.get_warns(ctx.guild.id, member.id)
        
        embed = discord.Embed(
            title="⚠️ تم التحذير!",
            description=f"{member.mention} اتحذر!",
            color=Config.COLORS['warning']
        )
        embed.add_field(name="📝 السبب", value=reason, inline=True)
        embed.add_field(name="🔢 عدد التحذيرات", value=f"{len(warns)}", inline=True)
        embed.add_field(name="👮 بواسطة", value=ctx.author.mention, inline=True)
        
        await ctx.send(embed=embed)
        await self.log_action(ctx.guild, "تحذير", ctx.author, member, reason, الرقم=warn_id)
        
        # محاولة إرسال رسالة
        try:
            dm_embed = discord.Embed(
                title="⚠️ تحذير",
                description=f"اتحذرت في **{ctx.guild.name}**\n**السبب:** {reason}\n**عدد التحذيرات:** {len(warns)}",
                color=Config.COLORS['warning']
            )
            await member.send(embed=dm_embed)
        except:
            pass
        
        # عقوبات تلقائية
        if len(warns) >= 3:
            await member.timeout(duration=3600, reason=f"تجاوز 3 تحذيرات")
            await ctx.send(f"🔇 {member.mention} اتكتم ساعة عشان تجاوز 3 تحذيرات!")
        elif len(warns) >= 5:
            await member.kick(reason="تجاوز 5 تحذيرات")
            await ctx.send(f"👢 {member.mention} اتطرد عشان تجاوز 5 تحذيرات!")
    
    @commands.command(name='التحذيرات', aliases=['warns', 'warnings'])
    async def warnings(self, ctx: commands.Context, member: discord.Member = None):
        """عرض التحذيرات"""
        member = member or ctx.author
        
        warns = await db.get_warns(ctx.guild.id, member.id)
        
        if not warns:
            await ctx.send(f"✅ {member.mention} مفيش عنده تحذيرات!")
            return
        
        embed = discord.Embed(
            title=f"⚠️ تحذيرات {member.display_name}",
            description=f"إجمالي التحذيرات: **{len(warns)}**",
            color=Config.COLORS['warning']
        )
        
        for i, warn in enumerate(warns[:25], 1):
            moderator = ctx.guild.get_member(warn['moderator_id'])
            mod_str = moderator.mention if moderator else f"<@{warn['moderator_id']}>"
            
            embed.add_field(
                name=f"#{i} - {warn['reason'][:50]}",
                value=f"👮 بواسطة: {mod_str}\n📅 <t:{warn['timestamp']}:R>",
                inline=True
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='مسح_التحذيرات', aliases=['clearwarns'])
    @commands.has_permissions(manage_messages=True)
    async def clear_warnings(self, ctx: commands.Context, member: discord.Member):
        """مسح كل تحذيرات عضو"""
        warns = await db.get_warns(ctx.guild.id, member.id)
        
        if not warns:
            await ctx.send(f"✅ {member.mention} مفيش عنده تحذيرات!")
            return
        
        if not await confirm_action(ctx, f"متأكد إنك عايز تمسح كل تحذيرات {member.mention} ({len(warns)} تحذير)؟"):
            await ctx.send("❌ تم الإلغاء")
            return
        
        await db.clear_warns(ctx.guild.id, member.id)
        
        embed = create_success_embed(
            "✅ تم المسح!",
            f"تم مسح **{len(warns)}** تحذير من {member.mention}"
        )
        await ctx.send(embed=embed)
        await self.log_action(ctx.guild, "مسح تحذيرات", ctx.author, member, العدد=len(warns))
    
    @commands.command(name='السجلات', aliases=['logs'])
    @commands.has_permissions(manage_guild=True)
    async def view_logs(self, ctx: commands.Context, limit: int = 20):
        """عرض السجلات"""
        limit = min(limit, 100)
        
        rows = await db.fetch(
            'SELECT * FROM logs WHERE guild_id = ? ORDER BY timestamp DESC LIMIT ?',
            (ctx.guild.id, limit)
        )
        
        if not rows:
            await ctx.send("❌ مفيش سجلات!")
            return
        
        embed = discord.Embed(
            title=f"📜 سجلات السيرفر (آخر {limit})",
            color=Config.COLORS['info']
        )
        
        for row in rows[:20]:
            id_, guild_id, event_type, user_id, target_id, details, timestamp = row
            
            user = ctx.guild.get_member(user_id)
            user_str = user.mention if user else f"<@{user_id}>"
            
            target_str = ""
            if target_id:
                target = ctx.guild.get_member(target_id)
                target_str = f" → {target.mention if target else f'<@{target_id}>'}"
            
            embed.add_field(
                name=f"{event_type}",
                value=f"👤 {user_str}{target_str}\n📅 <t:{timestamp}:R>",
                inline=False
            )
        
        await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))