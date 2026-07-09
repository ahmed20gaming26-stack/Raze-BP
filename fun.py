import discord
from discord.ext import commands
import random
import aiohttp
from config import Config

class Fun(commands.Cog, name="🎮 الترفيه"):
    """أوامر الترفيه"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._8ball_responses = [
            "نعم ✅", "لا ❌", "أكيد 💯", "أبداً ❌",
            "ربنا يعلم 🧐", "مش عارف 🤷", "بعدين 😅", "بالطبع 🎉",
            "ممكن 🤔", "مستحيل 💀", "اكيد لأ 🙅", "يلا بينا 🏃",
            "فكر تاني 🤔", "ثقة 100% 💯", "لا أعتقد 🤨", "حلمك 😴",
        ]
    
    @commands.command(name='نرد', aliases=['roll', 'رمي'])
    async def roll(self, ctx: commands.Context, sides: int = 6, count: int = 1):
        """رمي النرد"""
        if sides < 2 or sides > 1000:
            await ctx.send("❌ عدد الأوجه بين 2 و 1000")
            return
        
        if count < 1 or count > 10:
            await ctx.send("❌ عدد النرد بين 1 و 10")
            return
        
        results = [random.randint(1, sides) for _ in range(count)]
        total = sum(results)
        
        embed = discord.Embed(
            title="🎲 رمي النرد",
            color=Config.COLORS['info']
        )
        embed.add_field(name="🎯 النتائج", value=" | ".join(map(str, results)))
        embed.add_field(name="📊 المجموع", value=f"**{total}**")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='حظ', aliases=['8ball', 'كرة_الحظ'])
    async def eightball(self, ctx: commands.Context, *, question: str):
        """كرة الحظ"""
        response = random.choice(self._8ball_responses)
        
        embed = discord.Embed(
            title="🎱 كرة الحظ",
            color=Config.COLORS['purple']
        )
        embed.add_field(name="❓ سؤالك", value=question, inline=False)
        embed.add_field(name="✨ الإجابة", value=response, inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='عملة', aliases=['coin', 'coinflip'])
    async def coinflip(self, ctx: commands.Context):
        """رمي العملة"""
        result = random.choice(['وجه 🪙', 'كتابة 🪙'])
        await ctx.send(f"🪙 النتيجة: **{result}**")
    
    @commands.command(name='اختيار', aliases=['choice', 'pick'])
    async def choice(self, ctx: commands.Context, *, options: str):
        """اختيار عشوائي من خيارات"""
        options_list = [opt.strip() for opt in options.split(',') if opt.strip()]
        
        if len(options_list) < 2:
            await ctx.send("❌ لازم يكون في خيارين على الأقل! مثال: `!اختيار تفاح, موز, برتقال`")
            return
        
        chosen = random.choice(options_list)
        
        embed = discord.Embed(
            title="🎲 الاختيار العشوائي",
            description=f"🎯 اخترت: **{chosen}**",
            color=Config.COLORS['primary']
        )
        embed.add_field(name="📝 الخيارات", value='\n'.join([f"• {opt}" for opt in options_list]))
        
        await ctx.send(embed=embed)
    
    @commands.command(name='ميمز', aliases=['meme', 'ميم'])
    async def meme(self, ctx: commands.Context):
        """عرض ميم عشوائي"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get('https://meme-api.com/gimme') as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        embed = discord.Embed(
                            title=data.get('title', 'ميم'),
                            url=data.get('postLink', ''),
                            color=Config.COLORS['info']
                        )
                        embed.set_image(url=data.get('url', ''))
                        embed.set_footer(text=f"👍 {data.get('ups', 0)} | r/{data.get('subreddit', '')}")
                        
                        await ctx.send(embed=embed)
                    else:
                        await ctx.send("❌ مش قادر أجيب ميم دلوقتي!")
            except Exception as e:
                await ctx.send(f"❌ خطأ: {str(e)}")
    
    @commands.command(name='قط', aliases=['cat', 'قطة'])
    async def cat(self, ctx: commands.Context):
        """صورة قطة عشوائية"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get('https://api.thecatapi.com/v1/images/search') as response:
                    if response.status == 200:
                        data = await response.json()
                        url = data[0]['url']
                        
                        embed = discord.Embed(
                            title="🐱 قطة عشوائية!",
                            color=Config.COLORS['info']
                        )
                        embed.set_image(url=url)
                        
                        await ctx.send(embed=embed)
                    else:
                        await ctx.send("❌ مش قادر أجيب صورة قطة!")
            except Exception as e:
                await ctx.send(f"❌ خطأ: {str(e)}")
    
    @commands.command(name='كلب', aliases=['dog', 'جرو'])
    async def dog(self, ctx: commands.Context):
        """صورة كلب عشوائية"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get('https://dog.ceo/api/breeds/image/random') as response:
                    if response.status == 200:
                        data = await response.json()
                        url = data['message']
                        
                        embed = discord.Embed(
                            title="🐶 كلب عشوائي!",
                            color=Config.COLORS['info']
                        )
                        embed.set_image(url=url)
                        
                        await ctx.send(embed=embed)
                    else:
                        await ctx.send("❌ مش قادر أجيب صورة كلب!")
            except Exception as e:
                await ctx.send(f"❌ خطأ: {str(e)}")
    
    @commands.command(name='حقيقة_او_جرأة', aliases=['truth_dare', 'td'])
    async def truth_dare(self, ctx: commands.Context, choice: str = None):
        """حقيقة أو جرأة"""
        truths = [
            "ما هو أكبر سر خبيته عن أهلك؟",
            "مين آخر شخص فكرت فيه قبل النوم؟",
            "ما هو أكثر موقف محرج حصلك؟",
            "لو تقدر تغير حاجة في نفسك هتغير إيه؟",
            "مين الشخص اللي تتمنى تقابله؟",
            "ما هو أكبر خوف عندك؟",
            "لو مفيش قوانين هتعمل إيه؟",
            "مين أكتر شخص بتحبه في السيرفر؟",
        ]
        
        dares = [
            "ابعت رسالة حب لآخر شخص في DMs",
            "غير اسمك لـ 'أنا غبي' لمدة 10 دقايق",
            "اعمل 10 ضغط",
            "ابعت صورة قطتك/كلبك",
            "قلد شخصية كرتونية مشهورة",
            "اتصل بصديقك وغني له أغنية",
            "اعترف بحاجه محرجة حصلتلك",
            "ارقص لمدة 30 ثانية",
        ]
        
        if choice and choice.lower() in ['حقيقة', 'truth', 't']:
            text = random.choice(truths)
            title = "🤔 حقيقة"
        elif choice and choice.lower() in ['جرأة', 'dare', 'd']:
            text = random.choice(dares)
            title = "😈 جرأة"
        else:
            if random.choice([True, False]):
                text = random.choice(truths)
                title = "🤔 حقيقة"
            else:
                text = random.choice(dares)
                title = "😈 جرأة"
        
        embed = discord.Embed(
            title=title,
            description=text,
            color=Config.COLORS['purple']
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='شخصية_انمي', aliases=['anime'])
    async def anime_character(self, ctx: commands.Context):
        """شخصية أنمي عشوائية"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get('https://api.jikan.moe/v4/characters') as response:
                    if response.status == 200:
                        data = await response.json()
                        char = random.choice(data['data'])
                        
                        embed = discord.Embed(
                            title=f"🎌 {char['name']}",
                            url=char['url'],
                            color=Config.COLORS['purple']
                        )
                        
                        if char['images']['jpg']['image_url']:
                            embed.set_image(url=char['images']['jpg']['image_url'])
                        
                        if char.get('name_kanji'):
                            embed.add_field(name="📝 بالياباني", value=char['name_kanji'], inline=True)
                        
                        if char.get('favorites'):
                            embed.add_field(name="⭐ الشعبية", value=f"{char['favorites']:,}", inline=True)
                        
                        await ctx.send(embed=embed)
                    else:
                        await ctx.send("❌ مش قادر أجيب شخصية!")
            except Exception as e:
                await ctx.send(f"❌ خطأ: {str(e)}")
    
    @commands.command(name='اقتباس', aliases=['quote'])
    async def quote(self, ctx: commands.Context):
        """اقتباس عشوائي"""
        quotes = [
            ("النجاح ليس نهائياً، والفشل ليس قاتلاً: الشجاعة للاستمرار هي ما يهم", "ونستون تشرشل"),
            ("الحياة ليست عن إيجاد نفسك. الحياة عن صنع نفسك", "جورج برنارد شو"),
            ("كن التغيير الذي تريد أن تراه في العالم", "ماهاتما غاندي"),
            ("الطريقة الوحيدة للقيام بعمل عظيم هي أن تحب ما تفعله", "ستيف جوبز"),
            ("لا تحكم على كل يوم بالحصاد الذي تجنيه، بل بالبذور التي تزرعها", "روبرت لويس ستيفنسون"),
            ("المستقبل ملك لمن يؤمن بجمال أحلامه", "إليانور روزفلت"),
            ("كن نفسك؛ كل شخص آخر موجود بالفعل", "أوسكار وايلد"),
            ("في وسط الصعوبة تكمن الفرصة", "ألبرت أينشتاين"),
        ]
        
        text, author = random.choice(quotes)
        
        embed = discord.Embed(
            title="💭 اقتباس اليوم",
            description=f"\"{text}\"",
            color=Config.COLORS['primary']
        )
        embed.set_footer(text=f"— {author}")
        
        await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Fun(bot))