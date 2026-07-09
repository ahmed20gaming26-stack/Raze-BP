import discord
from discord.ext import commands
import time
from database import db
from config import Config
from utils.helpers import format_time

class AFK(commands.Cog, name="💤 نظام AFK"):
    """نظام الابتعاد"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """فحص الرسائل للـ AFK"""
        if message.author.bot or not message.guild:
            return
        
        # فحص إذا كان المرسل عليه AFK
        afk_data = await db.fetch(
            'SELECT * FROM afk WHERE user_id = ? AND guild_id = ?',
            (message.author.id, message.guild.id)
        )
        
        if afk_data:
            # إزالة AFK
            await db.execute(
                'DELETE FROM afk WHERE user_id = ? AND guild_id = ?',
                (message.author.id, message.guild.id)
            )
            
            afk_time = int(time.time()) - afk_data[0][3]
            
            msg = await message.channel.send(
                f"👋 **أهلاً بعودتك {message.author.mention}!** كنت AFK لمدة **{format_time(afk_time)}**",
                delete_after=5
            )
            
            # تغيير اسم العضو
            member = message.author
            if member.display_name.startswith("[AFK]"):
                new_name = member.display_name[6:]
                try:
                    await member.edit(nick=new_name)
                except:
                    pass
        
        # فحص إذا كان مذكور شخص AFK
        for mention in message.mentions:
            if mention.bot:
                continue
            
            afk_data = await db.fetch(
                'SELECT * FROM afk WHERE user_id = ? AND guild_id = ?',
                (mention.id, message.guild.id)
            )
            
            if afk_data:
                reason = afk_data[0][2]
                afk_time = int(time.time()) - afk_data[0][3]
                
                embed = discord.Embed(
                    title="💤 المستخدم AFK",
                    description=(
                        f"**{mention.display_name}** مش موجود دلوقتي 💤\n"
                        f"**📝 السبب:** {reason}\n"
                        f"**⏰ منذ:** {format_time(afk_time)}"
                    ),
                    color=Config.COLORS['info']
                )
                
                await message.channel.send(embed=embed, delete_after=10)
    
    @commands.command(name='afk', aliases=['ابتعاد', 'مشغول'])
    async def afk(self, ctx: commands.Context, *, reason: str = "مفيش سبب"):
        """تعيين AFK"""
        # فحص إذا كان AFK بالفعل
        existing = await db.fetch(
            'SELECT * FROM afk WHERE user_id = ? AND guild_id = ?',
            (ctx.author.id, ctx.guild.id)
        )
        
        if existing:
            await ctx.send(f"❌ انت AFK بالفعل! اكتب رسالة لإلغاء AFK")
            return
        
        # حفظ AFK
        await db.execute(
            'INSERT INTO afk (user_id, guild_id, reason, timestamp) VALUES (?, ?, ?, ?)',
            (ctx.author.id, ctx.guild.id, reason, int(time.time()))
        )
        
        # تغيير الاسم
        try:
            if not ctx.author.display_name.startswith("[AFK]"):
                await ctx.author.edit(nick=f"[AFK] {ctx.author.display_name}")
        except:
            pass
        
        embed = discord.Embed(
            title="💤 AFK",
            description=f"صرت AFK!\n**📝 السبب:** {reason}",
            color=Config.COLORS['info']
        )
        embed.set_footer(text="اكتب أي رسالة لإلغاء AFK")
        
        await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(AFK(bot))