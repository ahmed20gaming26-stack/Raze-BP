import discord
from discord.ext import commands, tasks
import random
import time
from database import db
from config import Config
from utils.helpers import format_time, get_timestamp

class GiveawayView(discord.ui.View):
    """عرض المسابقة"""
    def __init__(self, giveaway_id: int, entries: int = 0):
        super().__init__(timeout=None)
        self.giveaway_id = giveaway_id
        self.entries = entries
        self.ended = False
    
    @discord.ui.button(label="🎁 شارك", style=discord.ButtonStyle.success, custom_id='enter')
    async def enter(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.ended:
            await interaction.response.send_message("❌ المسابقة انتهت!", ephemeral=True)
            return
        
        # إضافة للمشاركين (في قاعدة البيانات)
        await db.execute(
            'INSERT OR IGNORE INTO giveaway_entries (giveaway_id, user_id) VALUES (?, ?)',
            (self.giveaway_id, interaction.user.id)
        )
        
        self.entries += 1
        button.label = f"🎁 شارك ({self.entries})"
        
        await interaction.response.edit_message(view=self)
        await interaction.followup.send("✅ تم تسجيل مشاركتك!", ephemeral=True)

class Giveaways(commands.Cog, name="🎁 المسابقات"):
    """نظام المسابقات"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.check_giveaways.start()
    
    def cog_unload(self):
        self.check_giveaways.cancel()
    
    @tasks.loop(seconds=30)
    async def check_giveaways(self):
        """فحص المسابقات المنتهية"""
        current_time = int(time.time())
        
        rows = await db.fetch(
            'SELECT * FROM giveaways WHERE end_time <= ? AND ended = 0',
            (current_time,)
        )
        
        for row in rows:
            msg_id, guild_id, channel_id, host_id, prize, winners_count, end_time, requirements, ended = row
            
            guild = self.bot.get_guild(guild_id)
            if not guild:
                continue
            
            channel = guild.get_channel(channel_id)
            if not channel:
                continue
            
            try:
                message = await channel.fetch_message(msg_id)
            except:
                continue
            
            # جلب المشاركين
            entries = await db.fetch(
                'SELECT user_id FROM giveaway_entries WHERE giveaway_id = ?',
                (msg_id,)
            )
            
            user_ids = [row[0] for row in entries]
            
            if len(user_ids) < winners_count:
                embed = discord.Embed(
                    title="🎁 انتهت المسابقة!",
                    description=f"**الجائزة:** {prize}\n\n😔 مفيش مشاركين كفاية!",
                    color=Config.COLORS['error']
                )
            else:
                winners = random.sample(user_ids, min(winners_count, len(user_ids)))
                winner_mentions = [f"<@!{uid}>" for uid in winners]
                
                embed = discord.Embed(
                    title="🎉 انتهت المسابقة!",
                    description=(
                        f"**الجائزة:** {prize}\n"
                        f"**🏆 الفائزين:** {', '.join(winner_mentions)}\n"
                        f"**👥 عدد المشاركين:** {len(user_ids)}"
                    ),
                    color=Config.COLORS['success']
                )
                
                # إرسال رسالة للفائزين
                await channel.send(
                    f"🎉 مبروك {', '.join(winner_mentions)}! كسبتوا **{prize}**!"
                )
            
            embed.set_footer(text="انتهت المسابقة")
            
            try:
                await message.edit(embed=embed, view=None)
            except:
                pass
            
            await db.execute(
                'UPDATE giveaways SET ended = 1 WHERE message_id = ?',
                (msg_id,)
            )
    
    @check_giveaways.before_loop
    async def before_check_giveaways(self):
        await self.bot.wait_until_ready()
    
    @commands.command(name='مسابقة', aliases=['giveaway', 'قرعة'])
    @commands.has_permissions(manage_messages=True)
    async def giveaway(self, ctx: commands.Context, duration: str, winners: int, *, prize: str):
        """إنشاء مسابقة جديدة"""
        from utils.helpers import parse_time
        
        seconds = parse_time(duration)
        if not seconds or seconds <= 0:
            await ctx.send("❌ الوقت غلط! مثال: `10m`, `1h`, `1d`")
            return
        
        if winners < 1:
            await ctx.send("❌ عدد الفائزين لازم يكون أكبر من 0!")
            return
        
        end_time = int(time.time()) + seconds
        
        embed = discord.Embed(
            title="🎁 مسابقة جديدة!",
            description=(
                f"**🎁 الجائزة:** {prize}\n"
                f"**👥 عدد الفائزين:** {winners}\n"
                f"**⏰ تنتهي في:** {get_timestamp(end_time, 'R')}\n\n"
                f"**📝 للمشاركة:** اضغط على الزرار!"
            ),
            color=Config.COLORS['success']
        )
        embed.set_footer(text=f"بواسطة {ctx.author.display_name}")
        
        view = GiveawayView(0)  # سيتم تحديثه
        message = await ctx.send(embed=embed, view=view)
        
        # تحديث ID المسابقة
        view.giveaway_id = message.id
        view.entries = 0
        view.children[0].label = "🎁 شارك (0)"
        
        await message.edit(view=view)
        
        # حفظ في قاعدة البيانات
        await db.execute(
            'INSERT INTO giveaways (message_id, guild_id, channel_id, host_id, prize, winners_count, end_time, ended) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (message.id, ctx.guild.id, ctx.channel.id, ctx.author.id, prize, winners, end_time, 0)
        )
        
        await ctx.send(f"✅ تم بدء المسابقة! تنتهي بعد **{format_time(seconds)}**")

async def setup(bot: commands.Bot):
    # إنشاء جدول المشاركات
    await db.execute('''
        CREATE TABLE IF NOT EXISTS giveaway_entries (
            giveaway_id INTEGER,
            user_id INTEGER,
            PRIMARY KEY (giveaway_id, user_id)
        )
    ''')
    
    # فحص إذا كان العمود موجود بالفعل
    try:
        await db.execute('ALTER TABLE giveaways ADD COLUMN ended INTEGER DEFAULT 0')
    except Exception as e:
        if 'duplicate column name' not in str(e).lower():
            raise e
    
    await bot.add_cog(Giveaways(bot))