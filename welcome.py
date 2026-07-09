import discord
from discord.ext import commands
from database import db
from config import Config
from utils.helpers import get_timestamp

class Welcome(commands.Cog, name="👋 الترحيب"):
    """نظام الترحيب والمغادرة"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """عندما يدخل عضو جديد"""
        settings = await db.get_guild_settings(member.guild.id)
        welcome_channel_id = settings.get('welcome_channel')
        
        if not welcome_channel_id:
            return
        
        channel = member.guild.get_channel(welcome_channel_id)
        if not channel:
            return
        
        # رسالة ترحيب
        custom_message = settings.get('welcome_message') or (
            f"👋 **أهلاً بيك {member.mention} في {member.guild.name}!** 🎉\n\n"
            f"📊 **إحصائيات السيرفر:**\n"
            f"👥 الأعضاء: **{member.guild.member_count}**\n"
            f"📅 تاريخ الانضمام: {get_timestamp(int(member.joined_at.timestamp()))}\n\n"
            f"📋 **قوانين السيرفر:**\n"
            f"• احترم الجميع 🤝\n"
            f"• ممنوع السبام 🚫\n"
            f"• استمتع! 🎉"
        )
        
        # Embed ترحيبي
        embed = discord.Embed(
            title="👋 عضو جديد!",
            description=custom_message.replace('{member}', member.mention).replace('{server}', member.guild.name).replace('{count}', str(member.guild.member_count)),
            color=Config.COLORS['success']
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"المعرف: {member.id}")
        
        try:
            await channel.send(content=member.mention, embed=embed)
        except:
            pass
        
        # إعطاء الرتبة التلقائية
        autorole_id = settings.get('autorole_id')
        if autorole_id:
            role = member.guild.get_role(autorole_id)
            if role:
                try:
                    await member.add_roles(role, reason="Auto-role")
                except:
                    pass
        
        # رسالة خاصة للعضو
        try:
            dm_embed = discord.Embed(
                title=f"👋 أهلاً بيك في {member.guild.name}!",
                description=(
                    "نورت السيرفر! 🎉\n\n"
                    "**📋 القوانين:**\n"
                    "• احترم الجميع\n"
                    "• ممنوع السبام\n"
                    "• استمتع!\n\n"
                    f"**👥 عدد الأعضاء:** {member.guild.member_count}"
                ),
                color=Config.COLORS['primary']
            )
            
            if member.guild.icon:
                dm_embed.set_thumbnail(url=member.guild.icon.url)
            
            await member.send(embed=dm_embed)
        except:
            pass
    
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """عندما يخرج عضو"""
        settings = await db.get_guild_settings(member.guild.id)
        goodbye_channel_id = settings.get('goodbye_channel')
        
        if not goodbye_channel_id:
            return
        
        channel = member.guild.get_channel(goodbye_channel_id)
        if not channel:
            return
        
        custom_message = settings.get('goodbye_message') or (
            f"👋 **{member} ودعنا!** 😔\n"
            f"📊 عدد الأعضاء: **{member.guild.member_count}**"
        )
        
        embed = discord.Embed(
            title="👋 وداعًا!",
            description=custom_message.replace('{member}', str(member)).replace('{server}', member.guild.name).replace('{count}', str(member.guild.member_count)),
            color=Config.COLORS['error']
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        
        try:
            await channel.send(embed=embed)
        except:
            pass
    
    @commands.command(name='ترحيب_قناة', aliases=['setwelcome'])
    @commands.has_permissions(manage_guild=True)
    async def set_welcome_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        """تحديد قناة الترحيب"""
        await db.update_guild_setting(ctx.guild.id, 'welcome_channel', channel.id)
        await ctx.send(f"✅ تم تعيين قناة الترحيب إلى {channel.mention}")
    
    @commands.command(name='وداع_قناة', aliases=['setgoodbye'])
    @commands.has_permissions(manage_guild=True)
    async def set_goodbye_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        """تحديد قناة الوداع"""
        await db.update_guild_setting(ctx.guild.id, 'goodbye_channel', channel.id)
        await ctx.send(f"✅ تم تعيين قناة الوداع إلى {channel.mention}")
    
    @commands.command(name='رتبة_تلقائية', aliases=['setautorole'])
    @commands.has_permissions(manage_roles=True)
    async def set_autorole(self, ctx: commands.Context, role: discord.Role):
        """تحديد الرتبة التلقائية"""
        if role >= ctx.guild.me.top_role:
            await ctx.send("❌ الرتبة دي أعلى من رتبتي!")
            return
        
        await db.update_guild_setting(ctx.guild.id, 'autorole_id', role.id)
        await ctx.send(f"✅ تم تعيين الرتبة التلقائية إلى {role.mention}")

async def setup(bot: commands.Bot):
    await bot.add_cog(Welcome(bot))