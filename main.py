import discord
from discord.ext import commands
import asyncio
import sys
import traceback
import logging
from config import Config
from database import db

# إعداد الـ Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('bot')

# إعداد البوت
intents = discord.Intents.all()
bot = commands.Bot(
    command_prefix=Config.PREFIX,
    intents=intents,
    help_command=None,
    case_insensitive=True,
    owner_ids=set(Config.OWNER_IDS) if Config.OWNER_IDS else None,
)

@bot.event
async def on_ready():
    """عندما يكون البوت جاهز"""
    logger.info("=" * 60)
    logger.info(f"✅ البوت شغال! اسمي {bot.user}")
    logger.info(f"📊 في {len(bot.guilds)} سيرفر")
    logger.info(f"👥 يخدم {sum(g.member_count for g in bot.guilds)} عضو")
    logger.info(f"🔗 Discord.py Version: {discord.__version__}")
    logger.info("=" * 60)
    
    # تحميل الـ Cogs
    await load_cogs()
    
    # تغيير الحالة
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{len(bot.guilds)} سيرفر | !مساعدة"
        ),
        status=discord.Status.online
    )

async def load_cogs():
    """تحميل كل الـ Cogs"""
    cogs = [
        'cogs.admin',
        'cogs.economy',
        'cogs.levels',
        'cogs.moderation',
        'cogs.fun',
        'cogs.games',
        'cogs.tickets',
        'cogs.giveaways',
        'cogs.suggestions',
        'cogs.polls',
        'cogs.logs',
        'cogs.welcome',
        'cogs.afk',
        'cogs.reminders',
        'cogs.search',
        'cogs.utility',
        'cogs.owner',
        'cogs.music',
    ]
    
    loaded = 0
    failed = 0
    
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            logger.info(f"✅ تم تحميل {cog}")
            loaded += 1
        except Exception as e:
            logger.error(f"❌ فشل تحميل {cog}: {e}")
            traceback.print_exc()
            failed += 1
    
    logger.info(f"📦 تم تحميل {loaded} Cog بنجاح، فشل {failed}")

@bot.event
async def on_command_error(ctx: commands.Context, error: Exception):
    """معالجة الأخطاء"""
    # تجاهل أخطاء معينة
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.CheckFailure):
        await ctx.send("❌ مش مسموح ليك تستخدم الأمر ده!")
        return
    
    # أخطاء الأوامر
    if isinstance(error, commands.MissingPermissions):
        perms = ', '.join(error.missing_permissions)
        await ctx.send(f"❌ محتاج الصلاحيات دي: `{perms}`")
        return
    
    if isinstance(error, commands.BotMissingPermissions):
        perms = ', '.join(error.missing_permissions)
        await ctx.send(f"❌ أنا محتاج الصلاحيات دي: `{perms}`")
        return
    
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ ناقص معامل: `{error.param.name}`")
        return
    
    if isinstance(error, commands.BadArgument):
        await ctx.send(f"❌ المعامل غلط: {str(error)}")
        return
    
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏳ الأمر ده عليه cooldown! استنى {error.retry_after:.1f} ثانية")
        return
    
    if isinstance(error, commands.MemberNotFound):
        await ctx.send(f"❌ مش لاقي العضو: `{error.argument}`")
        return
    
    if isinstance(error, commands.ChannelNotFound):
        await ctx.send(f"❌ مش لاقي القناة: `{error.argument}`")
        return
    
    if isinstance(error, commands.RoleNotFound):
        await ctx.send(f"❌ مش لاقي الدور: `{error.argument}`")
        return
    
    # أخطاء عامة
    logger.error(f"خطأ في الأمر {ctx.command}: {error}")
    traceback.print_exception(type(error), error, error.__traceback__)
    
    await ctx.send(f"❌ حصلت مشكلة: {str(error)[:100]}")

@bot.event
async def on_guild_join(guild: discord.Guild):
    """عندما يدخل البوت سيرفر جديد"""
    logger.info(f"🎉 دخلت سيرفر جديد: {guild.name} ({guild.id})")
    
    # إرسال رسالة ترحيبية في أول قناة متاح فيها إرسال
    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            embed = discord.Embed(
                title="👋 أهلاً بيكم!",
                description=(
                    "أنا البوت الذكي العربي 🤖\n\n"
                    "**مميزاتي:**\n"
                    "• 📊 نظام مستويات متطور\n"
                    "• 💰 اقتصاد كامل (بنك، متجر، عمل)\n"
                    "• 🎫 نظام تذاكر تفاعلي\n"
                    "• 🎁 مسابقات بزرار\n"
                    "• 🛡️ إدارة متقدمة\n"
                    "• 🎮 ألعاب تفاعلية\n"
                    "• 📝 اقتراحات واستطلاعات\n"
                    "• 📊 سجلات كاملة\n\n"
                    "**اكتب `!مساعدة` عشان تشوف كل الأوامر!**"
                ),
                color=Config.COLORS['primary']
            )
            try:
                await channel.send(embed=embed)
                break
            except:
                continue

@bot.event
async def on_guild_remove(guild: discord.Guild):
    """عندما يخرج البوت من سيرفر"""
    logger.info(f"👋 خرجت من سيرفر: {guild.name} ({guild.id})")

async def main():
    """الدالة الرئيسية"""
    try:
        # الاتصال بقاعدة البيانات
        await db.connect()
        logger.info("✅ تم الاتصال بقاعدة البيانات")
        
        # تشغيل البوت
        await bot.start(Config.TOKEN)
    except KeyboardInterrupt:
        logger.info("🛑 البوت اتوقف")
    except discord.LoginFailure:
        logger.error("❌ التوكن غلط!")
    except Exception as e:
        logger.error(f"❌ خطأ: {e}")
        traceback.print_exc()
    finally:
        # إغلاق قاعدة البيانات
        await db.close()
        if not bot.is_closed():
            await bot.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass