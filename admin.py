import discord
from discord.ext import commands
from database import db
from config import Config
from utils.helpers import create_success_embed, confirm_action

class Admin(commands.Cog, name="⚙️ الإعدادات"):
    """أوامر إعدادات السيرفر"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.command(name='برمج_سيرفر', aliases=['setup', 'setupserver'])
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(administrator=True)
    async def setup_server(self, ctx: commands.Context):
        """برمجة السيرفر بالكامل"""
        if not await confirm_action(ctx, "⚠️ متأكد إنك عايز تبرمج السيرفر بالكامل؟ ده هينشئ قنوات وأدوار كتير!"):
            await ctx.send("❌ تم الإلغاء")
            return
        
        progress_msg = await ctx.send("🔄 **جاري البرمجة...** 0%")
        guild = ctx.guild
        
        # 1. إنشاء التصنيفات
        await progress_msg.edit(content="🔄 **جاري البرمجة...** 10% - إنشاء التصنيفات...")
        
        categories = {
            '📋 الإدارة': ['📢-الإعلانات', '📋-القوانين', '📊-السجلات', '💡-الاقتراحات'],
            '💬 المحادثات': ['💬-العامة', '🎮-الألعاب', '🎵-الموسيقى', '📸-الصور', '🤖-أوامر-البوت'],
            '🎫 الدعم': ['🎫-التذاكر', '❓-الأسئلة'],
            '🎤 الصوتيات': ['🎙️-المحادثة', '🎵-الموسيقى', '🎮-الألعاب']
        }
        
        created_channels = 0
        for cat_name, channels in categories.items():
            category = await guild.create_category(cat_name)
            for channel_name in channels:
                if '🎙️' in channel_name or '🎵' in channel_name and 'صوت' in cat_name:
                    await guild.create_voice_channel(channel_name, category=category)
                else:
                    await guild.create_text_channel(channel_name, category=category)
                created_channels += 1
        
        # 2. إنشاء الأدوار
        await progress_msg.edit(content="🔄 **جاري البرمجة...** 40% - إنشاء الأدوار...")
        
        roles = {
            '👑 المالك': discord.Color.gold(),
            '🛡️ مدير': discord.Color.red(),
            '🔰 مشرف': discord.Color.blue(),
            '🎖️ VIP': discord.Color.purple(),
            '👥 عضو': discord.Color.green(),
            '🤖 بوت': discord.Color.orange(),
            '🔇 مكتوم': discord.Color.dark_grey()
        }
        
        created_roles = []
        for role_name, color in roles.items():
            role = await guild.create_role(name=role_name, color=color)
            created_roles.append(role)
        
        # 3. إعداد القنوات
        await progress_msg.edit(content="🔄 **جاري البرمجة...** 70% - إعداد القنوات...")
        
        # قناة الترحيب
        welcome_channel = discord.utils.get(guild.text_channels, name='👋-الترحيب')
        if not welcome_channel:
            welcome_channel = await guild.create_text_channel('👋-الترحيب')
        
        # قناة القوانين
        rules_channel = discord.utils.get(guild.text_channels, name='📋-القوانين')
        if rules_channel:
            rules_embed = discord.Embed(
                title="📋 قوانين السيرفر",
                description=(
                    "1️⃣ **الاحترام** 🤝\n"
                    "• احترم جميع الأعضاء\n"
                    "• ممنوع الإهانة أو التنمر\n\n"
                    "2️⃣ **ممنوع السبام** 🚫\n"
                    "• لا ترسل رسائل متكررة\n"
                    "• لا ترسل إعلانات بدون إذن\n\n"
                    "3️⃣ **المحتوى المناسب** ✅\n"
                    "• ممنوع المحتوى غير اللائق\n"
                    "• حافظ على نظافة القنوات\n\n"
                    "4️⃣ **استمتع!** 🎉\n"
                    "• استمتع بوقتك في السيرفر\n"
                    "• شارك مع الآخرين"
                ),
                color=Config.COLORS['error']
            )
            await rules_channel.send(embed=rules_embed)
        
        # 4. حفظ الإعدادات
        await progress_msg.edit(content="🔄 **جاري البرمجة...** 90% - حفظ الإعدادات...")
        
        await db.update_guild_setting(guild.id, 'welcome_channel', welcome_channel.id)
        await db.update_guild_setting(guild.id, 'logs_channel', discord.utils.get(guild.text_channels, name='📊-السجلات').id if discord.utils.get(guild.text_channels, name='📊-السجلات') else None)
        await db.update_guild_setting(guild.id, 'suggestions_channel', discord.utils.get(guild.text_channels, name='💡-الاقتراحات').id if discord.utils.get(guild.text_channels, name='💡-الاقتراحات') else None)
        
        autorole = discord.utils.get(guild.roles, name='👥 عضو')
        if autorole:
            await db.update_guild_setting(guild.id, 'autorole_id', autorole.id)
        
        # 5. رسالة النجاح
        await progress_msg.edit(content="✅ **تم بنجاح!**")
        
        embed = discord.Embed(
            title="✅ **تم برمجة السيرفر بالكامل!**",
            description=(
                f"🎉 السيرفر جاهز!\n\n"
                f"📂 **{len(categories)}** تصنيف\n"
                f"📝 **{created_channels}** قناة\n"
                f"🎭 **{len(created_roles)}** دور\n"
                f"👥 **{guild.member_count}** عضو"
            ),
            color=Config.COLORS['success']
        )
        
        embed.add_field(
            name="🎯 الأنظمة المفعلة",
            value=(
                "✅ نظام المستويات\n"
                "✅ نظام الاقتصاد\n"
                "✅ نظام التذاكر\n"
                "✅ نظام المسابقات\n"
                "✅ نظام الاقتراحات\n"
                "✅ نظام السجلات\n"
                "✅ نظام الترحيب"
            ),
            inline=True
        )
        
        embed.add_field(
            name="🤖 الأوامر المهمة",
            value=(
                "`!مساعدة` - كل الأوامر\n"
                "`!فلوسي` - الرصيد\n"
                "`!رتبتي` - مستواك\n"
                "`!تذكرة` - فتح تذكرة\n"
                "`!اقتراح` - إرسال اقتراح"
            ),
            inline=True
        )
        
        await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Admin(bot))