import discord
from typing import Optional, List

class PaginationView(discord.ui.View):
    """عرض الصفحات"""
    def __init__(self, pages: List[discord.Embed], author_id: int, timeout: int = 180):
        super().__init__(timeout=timeout)
        self.pages = pages
        self.current_page = 0
        self.author_id = author_id
        self.message: Optional[discord.Message] = None
        
        # تعطيل الأزرار لو فيه صفحة واحدة
        if len(pages) <= 1:
            for child in self.children:
                child.disabled = True
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ الأزرار دي مش ليك!", ephemeral=True)
            return False
        return True
    
    async def update_message(self, interaction: discord.Interaction):
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                if child.custom_id == 'first':
                    child.disabled = self.current_page == 0
                elif child.custom_id == 'prev':
                    child.disabled = self.current_page == 0
                elif child.custom_id == 'next':
                    child.disabled = self.current_page == len(self.pages) - 1
                elif child.custom_id == 'last':
                    child.disabled = self.current_page == len(self.pages) - 1
        
        embed = self.pages[self.current_page]
        embed.set_footer(text=f"الصفحة {self.current_page + 1}/{len(self.pages)}")
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(emoji="⏮️", style=discord.ButtonStyle.secondary, custom_id='first')
    async def first_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = 0
        await self.update_message(interaction)
    
    @discord.ui.button(emoji="◀️", style=discord.ButtonStyle.primary, custom_id='prev')
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = max(0, self.current_page - 1)
        await self.update_message(interaction)
    
    @discord.ui.button(emoji="▶️", style=discord.ButtonStyle.primary, custom_id='next')
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = min(len(self.pages) - 1, self.current_page + 1)
        await self.update_message(interaction)
    
    @discord.ui.button(emoji="⏭️", style=discord.ButtonStyle.secondary, custom_id='last')
    async def last_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = len(self.pages) - 1
        await self.update_message(interaction)
    
    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except:
                pass


class ConfirmView(discord.ui.View):
    """عرض التأكيد"""
    def __init__(self, author_id: int, timeout: int = 60):
        super().__init__(timeout=timeout)
        self.author_id = author_id
        self.value: Optional[bool] = None
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ مش مسموح ليك!", ephemeral=True)
            return False
        return True
    
    @discord.ui.button(label="✅ تأكيد", style=discord.ButtonStyle.success, custom_id='confirm')
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        self.stop()
        await interaction.response.defer()
    
    @discord.ui.button(label="❌ إلغاء", style=discord.ButtonStyle.danger, custom_id='cancel')
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        self.stop()
        await interaction.response.defer()


class DropdownSelect(discord.ui.Select):
    """قائمة منسدلة"""
    def __init__(self, placeholder: str, options: List[discord.SelectOption], callback, author_id: int):
        super().__init__(placeholder=placeholder, options=options)
        self._callback = callback
        self.author_id = author_id
    
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ مش مسموح ليك!", ephemeral=True)
            return
        await self._callback(interaction, self.values[0])


class DropdownView(discord.ui.View):
    """عرض القائمة المنسدلة"""
    def __init__(self, placeholder: str, options: List[discord.SelectOption], callback, author_id: int, timeout: int = 180):
        super().__init__(timeout=timeout)
        self.add_item(DropdownSelect(placeholder, options, callback, author_id))