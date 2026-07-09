import discord
from discord.ext import commands
import random
import time
import json
from database import db
from utils.helpers import format_time, create_success_embed, create_error_embed, format_number
from config import Config
from utils.views import PaginationView

class Economy(commands.Cog, name="💰 الاقتصاد"):
    """نظام الاقتصاد المتقدم"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.jobs = [
            ("👨‍💻 مبرمج", 150, 400),
            ("👨‍⚕️ طبيب", 200, 500),
            ("👷 مهندس", 120, 350),
            ("👨‍🏫 مدرس", 100, 300),
            ("⚖️ محامي", 180, 450),
            ("🎨 فنان", 80, 250),
            ("🎵 موسيقي", 90, 280),
            ("👨‍🍳 شيف", 110, 320),
            ("🚗 سائق", 70, 200),
            ("🛠️ فني", 85, 240),
            ("📰 صحفي", 95, 270),
            ("🎭 ممثل", 130, 380),
        ]
        self.crime_outcomes = [
            ("✅ نجحت العملية! سرقت بنك", 500, 1500),
            ("✅ نجحت! سرقت محل مجوهرات", 300, 1000),
            ("✅ نجحت! سرقت سيارة", 200, 800),
            ("❌ امسكتك الشرطة!", -200, -500),
            ("❌ فشلت العملية!", -100, -300),
            ("❌ وقعت في فخ!", -150, -400),
        ]
    
    @commands.command(name='فلوسي', aliases=['رصيد', 'balance', 'بنكي'])
    async def balance(self, ctx: commands.Context, member: discord.Member = None):
        """عرض الرصيد"""
        member = member or ctx.author
        data = await db.get_user_economy(member.id)
        
        embed = discord.Embed(
            title=f"💰 محفظة {member.display_name}",
            color=Config.COLORS['primary']
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        
        embed.add_field(
            name="💵 المحفظة",
            value=f"`{format_number(data['balance'])}` جنيه",
            inline=True
        )
        embed.add_field(
            name="🏦 البنك",
            value=f"`{format_number(data['bank'])}` جنيه",
            inline=True
        )
        embed.add_field(
            name="💎 الإجمالي",
            value=f"`{format_number(data['balance'] + data['bank'])}` جنيه",
            inline=True
        )
        embed.add_field(
            name="📈 إجمالي الأرباح",
            value=f"`{format_number(data['total_earned'])}` جنيه",
            inline=True
        )
        embed.add_field(
            name="📉 إجمالي المصروفات",
            value=f"`{format_number(data['total_spent'])}` جنيه",
            inline=True
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='مكافأة', aliases=['daily', 'يومية'])
    async def daily(self, ctx: commands.Context):
        """المكافأة اليومية"""
        data = await db.get_user_economy(ctx.author.id)
        current_time = int(time.time())
        
        time_since = current_time - data['last_daily']
        if time_since < Config.ECONOMY['daily_cooldown']:
            remaining = Config.ECONOMY['daily_cooldown'] - time_since
            embed = create_error_embed(
                "⏳ استنى شوية!",
                f"المكافأة الجاية بعد: **{format_time(remaining)}**"
            )
            await ctx.send(embed=embed)
            return
        
        # حساب المكافأة
        bonus = random.randint(Config.ECONOMY['daily_min'], Config.ECONOMY['daily_max'])
        
        # مكافأة إضافية للستريك
        streak_days = time_since // Config.ECONOMY['daily_cooldown']
        if streak_days >= 7:
            bonus = int(bonus * 1.5)
            streak_text = f"\n🔥 **مكافأة ستريك 7 أيام!** (+50%)"
        else:
            streak_text = ""
        
        await db.update_balance(ctx.author.id, bonus)
        await db.execute(
            'UPDATE economy SET last_daily = ? WHERE user_id = ?',
            (current_time, ctx.author.id)
        )
        
        embed = create_success_embed(
            "🎁 المكافأة اليومية!",
            f"خدت **{bonus:,}** جنيه! 🎉{streak_text}"
        )
        embed.add_field(
            name="💵 رصيدك الجديد",
            value=f"`{data['balance'] + bonus:,}` جنيه"
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='شغل', aliases=['work', 'اشتغل'])
    @commands.cooldown(1, Config.ECONOMY['work_cooldown'], commands.BucketType.user)
    async def work(self, ctx: commands.Context):
        """العمل وكسب فلوس"""
        job, min_earn, max_earn = random.choice(self.jobs)
        earnings = random.randint(min_earn, max_earn)
        
        await db.update_balance(ctx.author.id, earnings)
        await db.execute(
            'UPDATE economy SET last_work = ? WHERE user_id = ?',
            (int(time.time()), ctx.author.id)
        )
        
        data = await db.get_user_economy(ctx.author.id)
        
        embed = create_success_embed(
            "💼 شغلت!",
            f"اشتغلت كـ **{job}** وخدت **{earnings:,}** جنيه!"
        )
        embed.add_field(name="💵 رصيدك", value=f"`{data['balance']:,}` جنيه")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='جريمة', aliases=['crime', 'اجرام'])
    @commands.cooldown(1, 1800, commands.BucketType.user)
    async def crime(self, ctx: commands.Context):
        """محاولة جريمة (مخاطرة!)"""
        outcome, min_val, max_val = random.choice(self.crime_outcomes)
        amount = random.randint(min(abs(min_val), abs(max_val)), max(abs(min_val), abs(max_val)))
        
        if amount > 0:
            await db.update_balance(ctx.author.id, amount)
            embed = create_success_embed(
                "🎉 نجحت الجريمة!",
                f"{outcome} وخدت **{amount:,}** جنيه!"
            )
        else:
            await db.update_balance(ctx.author.id, -amount)
            embed = create_error_embed(
                "👮 فشلت الجريمة!",
                f"{outcome} وخسرت **{amount:,}** جنيه!"
            )
        
        data = await db.get_user_economy(ctx.author.id)
        embed.add_field(name="💵 رصيدك", value=f"`{data['balance']:,}` جنيه")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='إيداع', aliases=['deposit', 'dep'])
    async def deposit(self, ctx: commands.Context, amount: str):
        """إيداع فلوس في البنك"""
        data = await db.get_user_economy(ctx.author.id)
        
        if amount.lower() in ['all', 'كل', 'الكل']:
            amount = data['balance']
        else:
            try:
                amount = int(amount)
            except ValueError:
                await ctx.send("❌ المبلغ غلط!")
                return
        
        if amount <= 0:
            await ctx.send("❌ المبلغ لازم يكون أكبر من 0")
            return
        
        if data['balance'] < amount:
            await ctx.send("❌ معاكش فلوس كفاية في المحفظة!")
            return
        
        await db.update_balance(ctx.author.id, -amount)
        await db.execute(
            'UPDATE economy SET bank = bank + ? WHERE user_id = ?',
            (amount, ctx.author.id)
        )
        
        embed = create_success_embed(
            "🏦 تم الإيداع!",
            f"أودعت **{amount:,}** جنيه في البنك"
        )
        embed.add_field(name="💵 المحفظة", value=f"`{data['balance'] - amount:,}` جنيه")
        embed.add_field(name="🏦 البنك", value=f"`{data['bank'] + amount:,}` جنيه")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='سحب', aliases=['withdraw', 'with'])
    async def withdraw(self, ctx: commands.Context, amount: str):
        """سحب فلوس من البنك"""
        data = await db.get_user_economy(ctx.author.id)
        
        if amount.lower() in ['all', 'كل', 'الكل']:
            amount = data['bank']
        else:
            try:
                amount = int(amount)
            except ValueError:
                await ctx.send("❌ المبلغ غلط!")
                return
        
        if amount <= 0:
            await ctx.send("❌ المبلغ لازم يكون أكبر من 0")
            return
        
        if data['bank'] < amount:
            await ctx.send("❌ مفيش فلوس كفاية في البنك!")
            return
        
        await db.update_balance(ctx.author.id, amount)
        await db.execute(
            'UPDATE economy SET bank = bank - ? WHERE user_id = ?',
            (amount, ctx.author.id)
        )
        
        embed = create_success_embed(
            "💵 تم السحب!",
            f"سحبت **{amount:,}** جنيه من البنك"
        )
        embed.add_field(name="💵 المحفظة", value=f"`{data['balance'] + amount:,}` جنيه")
        embed.add_field(name="🏦 البنك", value=f"`{data['bank'] - amount:,}` جنيه")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='تحويل', aliases=['give', 'هدية', 'send'])
    async def transfer(self, ctx: commands.Context, member: discord.Member, amount: int):
        """تحويل فلوس لشخص"""
        if member.bot:
            await ctx.send("❌ مش ممكن تحول لبوت!")
            return
        
        if member == ctx.author:
            await ctx.send("❌ مش ممكن تحول لنفسك!")
            return
        
        if amount <= 0:
            await ctx.send("❌ المبلغ لازم يكون أكبر من 0")
            return
        
        data = await db.get_user_economy(ctx.author.id)
        if data['balance'] < amount:
            await ctx.send("❌ معاكش فلوس كفاية!")
            return
        
        await db.update_balance(ctx.author.id, -amount)
        await db.update_balance(member.id, amount)
        
        embed = create_success_embed(
            "💸 تم التحويل!",
            f"حولت **{amount:,}** جنيه إلى {member.mention}"
        )
        embed.add_field(name="💵 رصيدك", value=f"`{data['balance'] - amount:,}` جنيه")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='سرقة', aliases=['rob', 'اسرق'])
    @commands.cooldown(1, 3600, commands.BucketType.user)
    async def rob(self, ctx: commands.Context, member: discord.Member):
        """محاولة سرقة شخص"""
        if member.bot:
            await ctx.send("❌ مش ممكن تسرق بوت!")
            return
        
        if member == ctx.author:
            await ctx.send("❌ مش ممكن تسرق نفسك!")
            return
        
        target_data = await db.get_user_economy(member.id)
        if target_data['balance'] < 100:
            await ctx.send("❌ الشخص ده مفيش معاه فلوس كفاية!")
            return
        
        # نسبة النجاح
        success_chance = random.random()
        
        if success_chance < Config.ECONOMY['rob_chance']:
            # نجح
            stolen = random.randint(50, min(500, target_data['balance']))
            await db.update_balance(ctx.author.id, stolen)
            await db.update_balance(member.id, -stolen)
            
            embed = create_success_embed(
                "🎉 نجحت السرقة!",
                f"سرقت **{stolen:,}** جنيه من {member.mention}!"
            )
        else:
            # فشل
            fine = random.randint(100, 300)
            await db.update_balance(ctx.author.id, -fine)
            
            embed = create_error_embed(
                "👮 فشلت السرقة!",
                f"امسكتك الشرطة! وغرمتك **{fine:,}** جنيه!"
            )
        
        data = await db.get_user_economy(ctx.author.id)
        embed.add_field(name="💵 رصيدك", value=f"`{data['balance']:,}` جنيه")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='كازينو', aliases=['gamble', 'قمار', 'رهان'])
    async def gamble(self, ctx: commands.Context, amount: int):
        """المقامرة"""
        if amount <= 0:
            await ctx.send("❌ المبلغ لازم يكون أكبر من 0")
            return
        
        data = await db.get_user_economy(ctx.author.id)
        if data['balance'] < amount:
            await ctx.send("❌ معاكش فلوس كفاية!")
            return
        
        # لعبة السلوت
        symbols = ['🍒', '🍋', '🍊', '🍇', '💎', '7️⃣']
        result = [random.choice(symbols) for _ in range(3)]
        
        result_str = ' | '.join(result)
        
        # حساب الربح
        if result[0] == result[1] == result[2]:
            if result[0] == '💎':
                winnings = amount * 10
            elif result[0] == '7️⃣':
                winnings = amount * 7
            else:
                winnings = amount * 5
            result_text = f"🎉 **جاك بوت!** ربحت **{winnings:,}** جنيه!"
            color = Config.COLORS['success']
        elif result[0] == result[1] or result[1] == result[2] or result[0] == result[2]:
            winnings = amount * 2
            result_text = f"✨ **اتنين متشابهين!** ربحت **{winnings:,}** جنيه!"
            color = Config.COLORS['success']
        else:
            winnings = -amount
            result_text = f"😔 **خسرت!** خسرت **{amount:,}** جنيه"
            color = Config.COLORS['error']
        
        await db.update_balance(ctx.author.id, winnings)
        
        embed = discord.Embed(
            title="🎰 الكازينو",
            description=f"**{result_str}**\n\n{result_text}",
            color=color
        )
        
        new_data = await db.get_user_economy(ctx.author.id)
        embed.add_field(name="💵 رصيدك", value=f"`{new_data['balance']:,}` جنيه")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='الاوائل', aliases=['leaderboard', 'top', 'ترتيب'])
    async def leaderboard(self, ctx: commands.Context):
        """لوحة المتصدرين في الاقتصاد"""
        rows = await db.fetch(
            'SELECT user_id, balance + bank as total FROM economy ORDER BY total DESC LIMIT 100'
        )
        
        if not rows:
            await ctx.send("❌ مفيش بيانات!")
            return
        
        pages = []
        medals = ['🥇', '🥈', '🥉']
        
        for i in range(0, len(rows), 10):
            chunk = rows[i:i+10]
            embed = discord.Embed(
                title="💰 أغنى الأعضاء",
                color=Config.COLORS['primary']
            )
            
            for j, row in enumerate(chunk):
                user_id, total = row
                rank = i + j + 1
                medal = medals[rank-1] if rank <= 3 else f"#{rank}"
                
                try:
                    user = await self.bot.fetch_user(user_id)
                    name = user.name
                except:
                    name = f"Unknown ({user_id})"
                
                embed.add_field(
                    name=f"{medal} {name}",
                    value=f"💎 **{total:,}** جنيه",
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
    await bot.add_cog(Economy(bot))