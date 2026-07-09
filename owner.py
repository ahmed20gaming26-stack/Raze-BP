import discord
from discord.ext import commands
import sys
import os
import io
import contextlib
from config import Config

class Owner(commands.Cog, name="👑 المالك"):
    """أوامر خاصة بالمالك"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    async def cog_check(self, ctx: commands.Context) -> bool:
        """فحص إذا كان المستخدم مالك"""
        if not Config.OWNER_IDS:
            return False
        return ctx.author.id in Config.OWNER_IDS
    
    @commands.command(name='تحميل', aliases=['load'])
    async def load_cog(self, ctx: commands.Context, *, cog: str):
        """تحميل Cog"""
        try:
            await self.bot.load_extension(f'cogs.{cog}')
            await ctx.send(f"✅ تم تحميل `{cog}`")
        except Exception as e:
            await ctx.send(f"❌ خطأ: {str(e)}")
    
    @commands.command(name='إلغاء_تحميل', aliases=['unload'])
    async def unload_cog(self, ctx: commands.Context, *, cog: str):
        """إلغاء تحميل Cog"""
        try:
            await self.bot.unload_extension(f'cogs.{cog}')
            await ctx.send(f"✅ تم إلغاء تحميل `{cog}`")
        except Exception as e:
            await ctx.send(f"❌ خطأ: {str(e)}")
    
    @commands.command(name='إعادة_تحميل', aliases=['reload'])
    async def reload_cog(self, ctx: commands.Context, *, cog: str):
        """إعادة تحميل Cog"""
        try:
            await self.bot.reload_extension(f'cogs.{cog}')
            await ctx.send(f"✅ تم إعادة تحميل `{cog}`")
        except Exception as e:
            await ctx.send(f"❌ خطأ: {str(e)}")
    
    @commands.command(name='إعادة', aliases=['restart'])
    async def restart(self, ctx: commands.Context):
        """إعادة تشغيل البوت"""
        await ctx.send("🔄 جاري إعادة التشغيل...")
        os.execv(sys.executable, ['python'] + sys.argv)
    
    @commands.command(name='إيقاف', aliases=['shutdown'])
    async def shutdown(self, ctx: commands.Context):
        """إيقاف البوت"""
        await ctx.send("👋 جاري الإيقاف...")
        await self.bot.close()
    
    @commands.command(name='تقييم', aliases=['eval'])
    async def eval_code(self, ctx: commands.Context, *, code: str):
        """تقييم كود Python"""
        # إزالة code blocks
        if code.startswith('```') and code.endswith('```'):
            code = '\n'.join(code.split('\n')[1:-1])
        
        env = {
            'bot': self.bot,
            'ctx': ctx,
            'channel': ctx.channel,
            'author': ctx.author,
            'guild': ctx.guild,
            'message': ctx.message,
        }
        
        env.update(globals())
        
        stdout = io.StringIO()
        
        try:
            with contextlib.redirect_stdout(stdout):
                exec(f'async def func():\n{code}', env)
                result = await env['func']()
                
                output = stdout.getvalue()
                
                if result is not None:
                    output += str(result)
                
                if not output:
                    output = "✅ تم التنفيذ بنجاح (لا يوجد ناتج)"
                
                if len(output) > 1900:
                    output = output[:1900] + "..."
                
                await ctx.send(f"```py\n{output}\n```")
        except Exception as e:
            await ctx.send(f"❌ خطأ:\n```py\n{str(e)}\n```")
    
    @commands.command(name='سيرفرات', aliases=['servers'])
    async def list_servers(self, ctx: commands.Context):
        """عرض كل السيرفرات"""
        embed = discord.Embed(
            title=f"📊 السيرفرات ({len(self.bot.guilds)})",
            color=Config.COLORS['primary']
        )
        
        for i, guild in enumerate(self.bot.guilds[:25], 1):
            embed.add_field(
                name=f"#{i} {guild.name}",
                value=f"👥 {guild.member_count} عضو\n🆔 `{guild.id}`",
                inline=True
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='غادر', aliases=['leave'])
    async def leave_guild(self, ctx: commands.Context, guild_id: int = None):
        """مغادرة سيرفر"""
        guild = self.bot.get_guild(guild_id) if guild_id else ctx.guild
        
        if not guild:
            await ctx.send("❌ مش لاقي السيرفر!")
            return
        
        await ctx.send(f"👋 جاري مغادرة {guild.name}...")
        await guild.leave()

async def setup(bot: commands.Bot):
    await bot.add_cog(Owner(bot))