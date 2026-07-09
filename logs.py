import discord
from discord.ext import commands
from database import db
from config import Config

class Logs(commands.Cog, name="📜 السجلات"):
    """نظام السجلات"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        """حذف رسالة"""
        if message.author.bot or not message.guild:
            return
        
        settings = await db.get_guild_settings(message.guild.id)
        logs_channel_id = settings.get('logs_channel')
        
        if not logs_channel_id:
            return
        
        channel = message.guild.get_channel(logs_channel_id)
        if not channel:
            return
        
        embed = discord.Embed(
            title="🗑️ رسالة محذوفة",
            description=f"**القناة:** {message.channel.mention}\n**المحتوى:** {message.content or '[لا يوجد]'}",
            color=Config.COLORS['error']
        )
        embed.set_author(name=message.author, icon_url=message.author.display_avatar.url)
        embed.set_footer(text=f"ID: {message.author.id}")
        
        try:
            await channel.send(embed=embed)
        except:
            pass
    
    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        """تعديل رسالة"""
        if before.author.bot or not before.guild:
            return
        
        if before.content == after.content:
            return
        
        settings = await db.get_guild_settings(before.guild.id)
        logs_channel_id = settings.get('logs_channel')
        
        if not logs_channel_id:
            return
        
        channel = before.guild.get_channel(logs_channel_id)
        if not channel:
            return
        
        embed = discord.Embed(
            title="✏️ رسالة معدلة",
            description=f"**القناة:** {before.channel.mention}\n[الرسالة]({after.jump_url})",
            color=Config.COLORS['warning']
        )
        embed.add_field(name="📝 قبل", value=before.content[:1024] or '[لا يوجد]', inline=False)
        embed.add_field(name="📝 بعد", value=after.content[:1024] or '[لا يوجد]', inline=False)
        embed.set_author(name=before.author, icon_url=before.author.display_avatar.url)
        
        try:
            await channel.send(embed=embed)
        except:
            pass
    
    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """تحديث عضو"""
        if not after.guild:
            return
        
        settings = await db.get_guild_settings(after.guild.id)
        logs_channel_id = settings.get('logs_channel')
        
        if not logs_channel_id:
            return
        
        channel = after.guild.get_channel(logs_channel_id)
        if not channel:
            return
        
        # تغيير الاسم
        if before.nick != after.nick:
            embed = discord.Embed(
                title="📝 تغيير الاسم المستعار",
                description=f"{after.mention}",
                color=Config.COLORS['info']
            )
            embed.add_field(name="📝 قبل", value=before.nick or '[لا يوجد]', inline=True)
            embed.add_field(name="📝 بعد", value=after.nick or '[لا يوجد]', inline=True)
            
            try:
                await channel.send(embed=embed)
            except:
                pass
        
        # تغيير الرتب
        if before.roles != after.roles:
            added_roles = [r for r in after.roles if r not in before.roles]
            removed_roles = [r for r in before.roles if r not in after.roles]
            
            if added_roles or removed_roles:
                embed = discord.Embed(
                    title="🎭 تغيير الرتب",
                    description=f"{after.mention}",
                    color=Config.COLORS['info']
                )
                
                if added_roles:
                    embed.add_field(name="➕ رتب مضافة", value=', '.join([r.mention for r in added_roles]), inline=False)
                
                if removed_roles:
                    embed.add_field(name="➖ رتب محذوفة", value=', '.join([r.mention for r in removed_roles]), inline=False)
                
                try:
                    await channel.send(embed=embed)
                except:
                    pass
    
    @commands.command(name='سجلات_قناة', aliases=['setlogs'])
    @commands.has_permissions(manage_guild=True)
    async def set_logs_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        """تحديد قناة السجلات"""
        await db.update_guild_setting(ctx.guild.id, 'logs_channel', channel.id)
        await ctx.send(f"✅ تم تعيين قناة السجلات إلى {channel.mention}")

async def setup(bot: commands.Bot):
    await bot.add_cog(Logs(bot))