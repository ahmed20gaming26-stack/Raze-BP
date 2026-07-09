import discord
from discord.ext import commands
from config import Config

class PollView(discord.ui.View):
    """عرض الاستطلاع"""
    def __init__(self, options: list, author_id: int):
        super().__init__(timeout=None)
        self.options = options
        self.author_id = author_id
        self.votes = {i: [] for i in range(len(options))}
        
        for i, option in enumerate(options):
            button = discord.ui.Button(
                label=f"{option} (0)",
                style=discord.ButtonStyle.secondary,
                custom_id=f'vote_{i}'
            )
            button.callback = self.make_callback(i)
            self.add_item(button)
    
    def make_callback(self, index: int):
        async def callback(interaction: discord.Interaction):
            # إزالة الصوت السابق
            for i, voters in self.votes.items():
                if interaction.user.id in voters:
                    voters.remove(interaction.user.id)
            
            # إضافة الصوت الجديد
            self.votes[index].append(interaction.user.id)
            
            # تحديث الأزرار
            for i, child in enumerate(self.children):
                if isinstance(child, discord.ui.Button):
                    child.label = f"{self.options[i]} ({len(self.votes[i])})"
                    if interaction.user.id in self.votes[i]:
                        child.style = discord.ButtonStyle.primary
                    else:
                        child.style = discord.ButtonStyle.secondary
            
            await interaction.response.edit_message(view=self)
            await interaction.followup.send(f"✅ تم التصويت لـ **{self.options[index]}**!", ephemeral=True)
        
        return callback

class Polls(commands.Cog, name="📊 الاستطلاعات"):
    """نظام الاستطلاعات"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.command(name='استطلاع', aliases=['poll', 'تصويت'])
    async def poll(self, ctx: commands.Context, question: str, *options: str):
        """إنشاء استطلاع"""
        if len(options) < 2:
            await ctx.send("❌ لازم يكون في خيارين على الأقل! مثال: `!استطلاع \"أيه أحسن؟\" خيار1 خيار2`")
            return
        
        if len(options) > 10:
            await ctx.send("❌ أقصى عدد خيارات هو 10!")
            return
        
        embed = discord.Embed(
            title=f"📊 {question}",
            description="اضغط على الزرار للتصويت!",
            color=Config.COLORS['info']
        )
        embed.set_footer(text=f"بواسطة {ctx.author.display_name}")
        
        view = PollView(list(options), ctx.author.id)
        await ctx.send(embed=embed, view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(Polls(bot))