import discord
from discord.ext import commands
import time
from database import db
from config import Config

class SuggestionView(discord.ui.View):
    """عرض الاقتراح"""
    def __init__(self, suggestion_id: int, author_id: int):
        super().__init__(timeout=None)
        self.suggestion_id = suggestion_id
        self.author_id = author_id
    
    @discord.ui.button(label="✅ موافقة", style=discord.ButtonStyle.success, custom_id='approve')
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ مش مسموح ليك!", ephemeral=True)
            return
        
        await db.execute(
            'UPDATE suggestions SET status = ? WHERE id = ?',
            ('approved', self.suggestion_id)
        )
        
        embed = interaction.message.embeds[0]
        embed.color = Config.COLORS['success']
        embed.set_footer(text=f"✅ تمت الموافقة بواسطة {interaction.user.display_name}")
        
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="❌ رفض", style=discord.ButtonStyle.danger, custom_id='reject')
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ مش مسموح ليك!", ephemeral=True)
            return
        
        await db.execute(
            'UPDATE suggestions SET status = ? WHERE id = ?',
            ('rejected', self.suggestion_id)
        )
        
        embed = interaction.message.embeds[0]
        embed.color = Config.COLORS['error']
        embed.set_footer(text=f"❌ تم الرفض بواسطة {interaction.user.display_name}")
        
        await interaction.response.edit_message(embed=embed, view=self)

class Suggestions(commands.Cog, name="💡 الاقتراحات"):
    """نظام الاقتراحات"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.command(name='اقتراح', aliases=['suggest', 'اقترح'])
    async def suggest(self, ctx: commands.Context, *, suggestion: str):
        """إرسال اقتراح"""
        settings = await db.get_guild_settings(ctx.guild.id)
        suggestions_channel_id = settings.get('suggestions_channel')
        
        if not suggestions_channel_id:
            await ctx.send("❌ قناة الاقتراحات مش معينة! استخدم `!اقتراح_قناة #القناة`")
            return
        
        channel = ctx.guild.get_channel(suggestions_channel_id)
        if not channel:
            await ctx.send("❌ قناة الاقتراحات مش موجودة!")
            return
        
        embed = discord.Embed(
            title="💡 اقتراح جديد",
            description=suggestion,
            color=Config.COLORS['info']
        )
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
        embed.set_footer(text=f"ID: {ctx.author.id}")
        
        view = SuggestionView(0, ctx.author.id)
        msg = await channel.send(embed=embed, view=view)
        
        # حفظ في قاعدة البيانات
        await db.execute(
            'INSERT INTO suggestions (guild_id, user_id, message_id, content, status, created_at) VALUES (?, ?, ?, ?, ?, ?)',
            (ctx.guild.id, ctx.author.id, msg.id, suggestion, 'pending', int(time.time()))
        )
        
        # تحديث view
        async with db.db.execute('SELECT last_insert_rowid()') as cursor:
            suggestion_id = (await cursor.fetchone())[0]
        
        view.suggestion_id = suggestion_id
        await msg.edit(view=view)
        
        # إضافة ريأكشنات
        await msg.add_reaction('✅')
        await msg.add_reaction('❌')
        
        await ctx.send(f"✅ تم إرسال اقتراحك في {channel.mention}!", delete_after=5)
        try:
            await ctx.message.delete()
        except:
            pass
    
    @commands.command(name='اقتراح_قناة', aliases=['setsuggestions'])
    @commands.has_permissions(manage_guild=True)
    async def set_suggestions_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        """تحديد قناة الاقتراحات"""
        await db.update_guild_setting(ctx.guild.id, 'suggestions_channel', channel.id)
        await ctx.send(f"✅ تم تعيين قناة الاقتراحات إلى {channel.mention}")

async def setup(bot: commands.Bot):
    await bot.add_cog(Suggestions(bot))