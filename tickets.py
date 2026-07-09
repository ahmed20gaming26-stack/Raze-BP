import discord
from discord.ext import commands
import time
from database import db
from config import Config
from utils.helpers import create_success_embed, create_error_embed, confirm_action

class TicketCloseView(discord.ui.View):
    """عرض إغلاق التذكرة"""
    def __init__(self, ticket_id: int, user_id: int):
        super().__init__(timeout=None)
        self.ticket_id = ticket_id
        self.user_id = user_id
    
    @discord.ui.button(label="🗑️ حذف", style=discord.ButtonStyle.danger, custom_id='delete')
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id and not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("❌ مش مسموح ليك!", ephemeral=True)
            return
        
        await interaction.response.defer()
        channel = interaction.channel
        await channel.delete()
    
    @discord.ui.button(label="📝 حفظ السجل", style=discord.ButtonStyle.primary, custom_id='save')
    async def save_transcript(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id and not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("❌ مش مسموح ليك!", ephemeral=True)
            return
        
        await interaction.response.send_message("📝 جاري حفظ السجل...", ephemeral=True)
        
        messages = []
        async for message in interaction.channel.history(limit=None, oldest_first=True):
            if message.author == interaction.guild.me:
                continue
            
            content = message.content or "[محتوى غير نصي]"
            attachments = [a.url for a in message.attachments]
            
            msg_text = f"[{message.created_at.strftime('%Y-%m-%d %H:%M:%S')}] {message.author}: {content}"
            if attachments:
                msg_text += f"\n📎 المرفقات: {', '.join(attachments)}"
            
            messages.append(msg_text)
        
        transcript = '\n'.join(messages)
        
        import io
        file = discord.File(io.BytesIO(transcript.encode('utf-8')), filename=f"ticket_{interaction.channel.id}.txt")
        
        await interaction.channel.send(file=file)
        await interaction.followup.send("✅ تم حفظ السجل!", ephemeral=True)

class TicketView(discord.ui.View):
    """عرض إنشاء تذكرة"""
    def __init__(self, guild_id: int):
        super().__init__(timeout=None)
        self.guild_id = guild_id
    
    @discord.ui.button(label="🎫 فتح تذكرة", style=discord.ButtonStyle.primary, custom_id='create_ticket', emoji='🎫')
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        existing = await db.fetch(
            'SELECT channel_id FROM tickets WHERE guild_id = ? AND user_id = ? AND status = ?',
            (interaction.guild.id, interaction.user.id, 'open')
        )
        
        if existing:
            channel = interaction.guild.get_channel(existing[0][0])
            if channel:
                await interaction.response.send_message(
                    f"❌ عندك تذكرة مفتوحة بالفعل في {channel.mention}!",
                    ephemeral=True
                )
                return
            else:
                await db.execute(
                    'UPDATE tickets SET status = ? WHERE channel_id = ?',
                    ('closed', existing[0][0])
                )
        
        category = discord.utils.get(interaction.guild.categories, name="🎫 التذاكر")
        if not category:
            category = await interaction.guild.create_category("🎫 التذاكر")
        
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            interaction.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)
        }
        
        for role in interaction.guild.roles:
            if role.permissions.administrator or role.permissions.manage_channels:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
        
        channel = await interaction.guild.create_text_channel(
            f"تذكرة-{interaction.user.name}",
            category=category,
            overwrites=overwrites
        )
        
        await db.execute(
            'INSERT INTO tickets (channel_id, guild_id, user_id, status, created_at) VALUES (?, ?, ?, ?, ?)',
            (channel.id, interaction.guild.id, interaction.user.id, 'open', int(time.time()))
        )
        
        embed = discord.Embed(
            title=f"🎫 تذكرة {interaction.user.display_name}",
            description=(
                "مرحبًا! تم فتح تذكرتك بنجاح 🎉\n\n"
                "**📋 التعليمات:**\n"
                "• اشرح مشكلتك بالتفصيل\n"
                "• فريق الدعم هيرد عليك قريبًا\n"
                "• استخدم الأزرار أدناه للتحكم في التذكرة\n\n"
                "**🆔 رقم التذكرة:** " + f"{channel.id}"
            ),
            color=Config.COLORS['primary']
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        
        view = TicketCloseView(channel.id, interaction.user.id)
        
        await channel.send(
            content=f"👋 {interaction.user.mention} | فريق الدعم: <@&{interaction.guild.id}>",
            embed=embed,
            view=view
        )
        
        await interaction.response.send_message(
            f"✅ تم فتح تذكرتك في {channel.mention}!",
            ephemeral=True
        )

class Tickets(commands.Cog, name="🎫 التذاكر"):
    """نظام التذاكر التفاعلي"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.command(name='تذكرة_لوحة', aliases=['ticketpanel'])
    @commands.has_permissions(manage_guild=True)
    async def ticket_panel(self, ctx: commands.Context):
        """إنشاء لوحة التذاكر"""
        embed = discord.Embed(
            title="🎫 نظام التذاكر",
            description=(
                "**مرحبًا بك في نظام الدعم!**\n\n"
                "إذا كنت بحاجة إلى مساعدة، اضغط على الزر أدناه لفتح تذكرة.\n"
                "فريق الدعم سيرد عليك في أقرب وقت.\n\n"
                "**📌 ملاحظات:**\n"
                "• لا تفتح أكثر من تذكرة واحدة\n"
                "• كن صبورًا وانتظر الرد\n"
                "• احترم فريق الدعم"
            ),
            color=Config.COLORS['primary']
        )
        
        view = TicketView(ctx.guild.id)
        await ctx.send(embed=embed, view=view)
        
        try:
            await ctx.message.delete()
        except discord.NotFound:
            pass
        except discord.Forbidden:
            pass
        except Exception:
            pass
    
    @commands.command(name='اغلق', aliases=['close'])
    async def close_ticket(self, ctx: commands.Context):
        """إغلاق التذكرة الحالية"""
        ticket = await db.fetch(
            'SELECT * FROM tickets WHERE channel_id = ? AND status = ?',
            (ctx.channel.id, 'open')
        )
        
        if not ticket:
            await ctx.send("❌ القناة دي مش تذكرة!")
            return
        
        user = ctx.guild.get_member(ticket[0][2])
        
        if not await confirm_action(ctx, "متأكد إنك عايز تقفل التذكرة دي؟"):
            await ctx.send("❌ تم الإلغاء")
            return
        
        await db.execute(
            'UPDATE tickets SET status = ?, closed_at = ?, closed_by = ? WHERE channel_id = ?',
            ('closed', int(time.time()), ctx.author.id, ctx.channel.id)
        )
        
        overwrites = ctx.channel.overwrites
        if user:
            overwrites[user] = discord.PermissionOverwrite(view_channel=True, send_messages=False)
        
        await ctx.channel.edit(overwrites=overwrites)
        
        embed = create_success_embed(
            "🔒 تم إغلاق التذكرة!",
            "التذكرة اتقفلت. استخدم الأزرار أدناه."
        )
        
        view = TicketCloseView(ctx.channel.id, ctx.author.id)
        await ctx.send(embed=embed, view=view)


    @commands.command(name='تذكرة', aliases=['ticket', 'دعم', 'مساعده'])
    async def ticket_command(self, ctx: commands.Context):
        """فتح تذكرة دعم"""
        
        # فحص إذا كان فيه تذكرة مفتوحة بالفعل
        existing = await db.fetch(
            'SELECT channel_id FROM tickets WHERE guild_id = ? AND user_id = ? AND status = ?',
            (ctx.guild.id, ctx.author.id, 'open')
        )
        
        if existing:
            channel = ctx.guild.get_channel(existing[0][0])
            if channel:
                await ctx.send(f"❌ عندك تذكرة مفتوحة بالفعل في {channel.mention}!")
                return
            else:
                await db.execute(
                    'UPDATE tickets SET status = ? WHERE channel_id = ?',
                    ('closed', existing[0][0])
                )
        
        # إنشاء التصنيف لو مش موجود
        category = discord.utils.get(ctx.guild.categories, name="🎫 التذاكر")
        if not category:
            try:
                category = await ctx.guild.create_category("🎫 التذاكر")
            except discord.Forbidden:
                await ctx.send("❌ مفيش صلاحية إنشاء تصنيفات!")
                return
        
        # إعداد الصلاحيات
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            ctx.author: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            ctx.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)
        }
        
        # إضافة الأدوار الإدارية
        for role in ctx.guild.roles:
            if role.permissions.administrator or role.permissions.manage_channels:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
        
        # إنشاء القناة
        try:
            channel = await ctx.guild.create_text_channel(
                f"تذكرة-{ctx.author.name}",
                category=category,
                overwrites=overwrites
            )
        except discord.Forbidden:
            await ctx.send("❌ مفيش صلاحية إنشاء قنوات!")
            return
        except Exception as e:
            await ctx.send(f"❌ حصل خطأ: {str(e)[:100]}")
            return
        
        # حفظ في قاعدة البيانات
        await db.execute(
            'INSERT INTO tickets (channel_id, guild_id, user_id, status, created_at) VALUES (?, ?, ?, ?, ?)',
            (channel.id, ctx.guild.id, ctx.author.id, 'open', int(time.time()))
        )
        
        # Embed الترحيب
        embed = discord.Embed(
            title=f"🎫 تذكرة {ctx.author.display_name}",
            description=(
                "مرحبًا! تم فتح تذكرتك بنجاح 🎉\n\n"
                "**📋 التعليمات:**\n"
                "• اشرح مشكلتك بالتفصيل\n"
                "• فريق الدعم هيرد عليك قريبًا\n"
                "• استخدم الأزرار أدناه للتحكم في التذكرة\n\n"
                "**🆔 رقم التذكرة:** " + f"{channel.id}"
            ),
            color=Config.COLORS['primary']
        )
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        
        view = TicketCloseView(channel.id, ctx.author.id)
        
        await channel.send(
            content=f"👋 {ctx.author.mention} | فريق الدعم: <@&{ctx.guild.id}>",
            embed=embed,
            view=view
        )
        
        # رسالة نجاح في القناة الأصلية
        success_embed = create_success_embed(
            "✅ تم فتح التذكرة!",
            f"تذكرتك جاهزة في {channel.mention}"
        )
        
        await ctx.send(embed=success_embed, delete_after=10)
        
        # مسح رسالة الأمر
        try:
            await ctx.message.delete()
        except:
            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(Tickets(bot))