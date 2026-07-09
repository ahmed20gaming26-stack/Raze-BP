import discord
from discord.ext import commands
import aiohttp
from config import Config

class Search(commands.Cog, name="🔍 البحث"):
    """أوامر البحث"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.command(name='ويكي', aliases=['wiki', 'wikipedia'])
    async def wikipedia(self, ctx: commands.Context, *, query: str):
        """البحث في ويكيبيديا"""
        async with aiohttp.ClientSession() as session:
            try:
                url = f"https://ar.wikipedia.org/api/rest_v1/page/summary/{query}"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        embed = discord.Embed(
                            title=data.get('title', query),
                            description=data.get('extract', 'لا يوجد وصف')[:2048],
                            url=data.get('content_urls', {}).get('desktop', {}).get('page', ''),
                            color=Config.COLORS['info']
                        )
                        
                        if 'thumbnail' in data and 'source' in data['thumbnail']:
                            embed.set_thumbnail(url=data['thumbnail']['source'])
                        
                        embed.set_footer(text="ويكيبيديا العربية")
                        
                        await ctx.send(embed=embed)
                    else:
                        await ctx.send("❌ مش لاقي النتيجة!")
            except Exception as e:
                await ctx.send(f"❌ خطأ: {str(e)}")
    
    @commands.command(name='ترجمة', aliases=['translate'])
    async def translate(self, ctx: commands.Context, target_lang: str, *, text: str):
        """ترجمة نص"""
        async with aiohttp.ClientSession() as session:
            try:
                url = f"https://api.mymemory.translated.net/get?q={text}&langpair=ar|{target_lang}"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get('responseStatus') == 200:
                            translated = data['responseData']['translatedText']
                            
                            embed = discord.Embed(
                                title="🌐 الترجمة",
                                color=Config.COLORS['info']
                            )
                            embed.add_field(name="📝 النص الأصلي", value=text[:1024], inline=False)
                            embed.add_field(name=f"🔤 الترجمة ({target_lang})", value=translated[:1024], inline=False)
                            
                            await ctx.send(embed=embed)
                        else:
                            await ctx.send("❌ مش قادر أترجم!")
                    else:
                        await ctx.send("❌ خطأ في الاتصال!")
            except Exception as e:
                await ctx.send(f"❌ خطأ: {str(e)}")
    
    @commands.command(name='طقس', aliases=['weather'])
    async def weather(self, ctx: commands.Context, *, city: str):
        """حالة الطقس"""
        async with aiohttp.ClientSession() as session:
            try:
                # استخدام Open-Meteo API (مجاني بدون مفتاح)
                geocode_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
                async with session.get(geocode_url) as response:
                    if response.status != 200:
                        await ctx.send("❌ مش لاقي المدينة!")
                        return
                    
                    geo_data = await response.json()
                    if not geo_data.get('results'):
                        await ctx.send("❌ مش لاقي المدينة!")
                        return
                    
                    location = geo_data['results'][0]
                    lat, lon = location['latitude'], location['longitude']
                    city_name = location['name']
                    
                    weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,weather_code,wind_speed_10m,relative_humidity_2m"
                    async with session.get(weather_url) as response:
                        if response.status != 200:
                            await ctx.send("❌ مش قادر أجيب حالة الطقس!")
                            return
                        
                        weather_data = await response.json()
                        current = weather_data['current']
                        
                        temp = current['temperature_2m']
                        humidity = current['relative_humidity_2m']
                        wind = current['wind_speed_10m']
                        code = current['weather_code']
                        
                        # تحويل الكود لوصف
                        weather_descriptions = {
                            0: "☀️ صافي",
                            1: "🌤️ صافي غالبًا",
                            2: "⛅ غائم جزئيًا",
                            3: "☁️ غائم",
                            45: "🌫️ ضباب",
                            48: "🌫️ ضباب متجمد",
                            51: "🌦️ رذاذ خفيف",
                            53: "🌦️ رذاذ معتدل",
                            55: "🌦️ رذاذ كثيف",
                            61: "🌧️ مطر خفيف",
                            63: "🌧️ مطر معتدل",
                            65: "🌧️ مطر غزير",
                            71: "🌨️ ثلج خفيف",
                            73: "🌨️ ثلج معتدل",
                            75: "🌨️ ثلج كثيف",
                            80: "🌦️ زخات خفيفة",
                            81: "🌦️ زخات معتدلة",
                            82: "🌦️ زخات كثيفة",
                            95: "⛈️ عاصفة رعدية",
                            96: "⛈️ عاصفة رعدية مع برد",
                            99: "⛈️ عاصفة رعدية شديدة",
                        }
                        
                        description = weather_descriptions.get(code, "🌡️ غير معروف")
                        
                        embed = discord.Embed(
                            title=f"🌤️ الطقس في {city_name}",
                            color=Config.COLORS['info']
                        )
                        embed.add_field(name="🌡️ الحالة", value=description, inline=True)
                        embed.add_field(name="🌡️ الحرارة", value=f"{temp}°C", inline=True)
                        embed.add_field(name="💧 الرطوبة", value=f"{humidity}%", inline=True)
                        embed.add_field(name="💨 الرياح", value=f"{wind} km/h", inline=True)
                        
                        await ctx.send(embed=embed)
            except Exception as e:
                await ctx.send(f"❌ خطأ: {str(e)}")
    
    @commands.command(name='صور_انترنت', aliases=['image', 'بحث_صور'])
    async def image(self, ctx: commands.Context, *, query: str):
        """البحث عن صور"""
        async with aiohttp.ClientSession() as session:
            try:
                # استخدام Unsplash API (مجاني)
                url = f"https://source.unsplash.com/1600x900/?{query}"
                
                embed = discord.Embed(
                    title=f"🖼️ صورة: {query}",
                    color=Config.COLORS['info']
                )
                embed.set_image(url=url)
                
                await ctx.send(embed=embed)
            except Exception as e:
                await ctx.send(f"❌ خطأ: {str(e)}")

async def setup(bot: commands.Bot):
    await bot.add_cog(Search(bot))