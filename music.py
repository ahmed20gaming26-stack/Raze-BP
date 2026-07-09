import discord
from discord.ext import commands
import asyncio
import yt_dlp
import os
import random
from config import Config

FFMPEG_PATH = r"C:\ffmpeg\bin\ffmpeg.exe"

if not os.path.exists(FFMPEG_PATH):
    print(f"⚠️ تحذير: FFmpeg مش موجود في {FFMPEG_PATH}")
else:
    print(f"✅ FFmpeg موجود في {FFMPEG_PATH}")

class MusicControlView(discord.ui.View):
    """أزرار التحكم في الموسيقى"""
    def __init__(self, player, destination):
        super().__init__(timeout=None)
        self.player = player
        self.destination = destination
    
    async def _send(self, target, content=None, embed=None, ephemeral=False):
        """دالة إرسال ذكية"""
        if isinstance(target, discord.Interaction):
            if target.response.is_done():
                await target.followup.send(content=content, embed=embed, ephemeral=ephemeral)
            else:
                await target.response.send_message(content=content, embed=embed, ephemeral=ephemeral)
        elif isinstance(target, commands.Context):
            await target.send(content=content, embed=embed)
        elif isinstance(target, discord.TextChannel):
            await target.send(content=content, embed=embed)
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not interaction.user.voice:
            await self._send(interaction, "❌ لازم تكون في قناة صوتية!", ephemeral=True)
            return False
        
        if interaction.guild.voice_client and interaction.user.voice.channel != interaction.guild.voice_client.channel:
            await self._send(interaction, "❌ لازم تكون في نفس القناة الصوتية!", ephemeral=True)
            return False
        
        return True
    
    @discord.ui.button(emoji="⏮️", style=discord.ButtonStyle.secondary, custom_id='previous')
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.player.history:
            await self._send(interaction, "❌ مفيش أغنية سابقة!", ephemeral=True)
            return
        
        last_song = self.player.history.pop()
        self.player.queue.insert(0, last_song)
        
        if interaction.guild.voice_client and interaction.guild.voice_client.is_playing():
            interaction.guild.voice_client.stop()
        
        await self._send(interaction, f"⏮️ رجوع لـ: **{last_song['title']}**")
    
    @discord.ui.button(emoji="⏯️", style=discord.ButtonStyle.primary, custom_id='play_pause')
    async def play_pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.guild.voice_client:
            await self._send(interaction, "❌ البوت مش في قناة صوتية!", ephemeral=True)
            return
        
        if interaction.guild.voice_client.is_playing():
            interaction.guild.voice_client.pause()
            self.player.is_paused = True
            await self._send(interaction, "⏸️ تم الإيقاف المؤقت")
        elif interaction.guild.voice_client.is_paused():
            interaction.guild.voice_client.resume()
            self.player.is_paused = False
            await self._send(interaction, "▶️ تم الاستكمال")
        else:
            if self.player.queue:
                await self.player.play_next(self.destination, interaction.guild.voice_client)
                await self._send(interaction, "▶️ تم التشغيل")
            else:
                await self._send(interaction, "❌ مفيش أغاني في القائمة!", ephemeral=True)
    
    @discord.ui.button(emoji="⏭️", style=discord.ButtonStyle.secondary, custom_id='next')
    async def next_song(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild.voice_client and interaction.guild.voice_client.is_playing():
            interaction.guild.voice_client.stop()
            await self._send(interaction, "⏭️ تم التخطي")
        else:
            await self._send(interaction, "❌ مفيش أغنية شغالة!", ephemeral=True)
    
    @discord.ui.button(emoji="🔀", style=discord.ButtonStyle.success, custom_id='shuffle')
    async def shuffle(self, interaction: discord.Interaction, button: discord.ui.Button):
        if len(self.player.queue) < 2:
            await self._send(interaction, "❌ مفيش أغاني كفاية!", ephemeral=True)
            return
        
        random.shuffle(self.player.queue)
        await self._send(interaction, f"🔀 تم خلط **{len(self.player.queue)}** أغنية!")
    
    @discord.ui.button(emoji="🔁", style=discord.ButtonStyle.success, custom_id='repeat')
    async def repeat(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.player.current_song:
            await self._send(interaction, "❌ مفيش أغنية شغالة!", ephemeral=True)
            return
        
        self.player.queue.insert(0, self.player.current_song.copy())
        await self._send(interaction, f"🔁 هتتكرر: **{self.player.current_song['title']}**")
    
    @discord.ui.button(emoji="⏹️", style=discord.ButtonStyle.danger, custom_id='stop')
    async def stop_all(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild.voice_client:
            self.player.queue.clear()
            self.player.history.clear()
            interaction.guild.voice_client.stop()
            await self._send(interaction, "⏹️ تم إيقاف كل حاجة")
        else:
            await self._send(interaction, "❌ البوت مش في قناة صوتية!", ephemeral=True)

class MusicSearchModal(discord.ui.Modal, title="🔍 البحث عن أغنية"):
    """نافذة البحث عن أغنية"""
    song_name = discord.ui.TextInput(
        label="اسم الأغنية",
        placeholder="مثال: despacito, ahmed gamal, shape of you...",
        required=True,
        max_length=100,
        style=discord.TextStyle.short
    )
    
    def __init__(self, cog, channel):
        super().__init__()
        self.cog = cog
        self.channel = channel
    
    async def on_submit(self, interaction: discord.Interaction):
        query = self.song_name.value.strip()
        
        if not query:
            await interaction.response.send_message("❌ لازم تكتب اسم الأغنية!", ephemeral=True)
            return
        
        if not interaction.user.voice:
            await interaction.response.send_message("❌ لازم تكون في قناة صوتية!", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        player = self.cog.get_player(interaction.guild.id)
        
        # لو البوت مش في قناة، يدخل
        if not interaction.guild.voice_client or not interaction.guild.voice_client.is_connected():
            try:
                await interaction.user.voice.channel.connect()
                await asyncio.sleep(1)
            except Exception as e:
                await interaction.followup.send(f"❌ فشل الاتصال: {str(e)[:100]}", ephemeral=True)
                return
        
        if not interaction.guild.voice_client:
            await interaction.followup.send("❌ فشل الاتصال!", ephemeral=True)
            return
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
        }
        
        try:
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(
                None,
                lambda: yt_dlp.YoutubeDL(ydl_opts).extract_info(f"ytsearch:1 {query}", download=False)
            )
            
            if 'entries' in info and info['entries']:
                info = info['entries'][0]
            
            song_data = {
                'url': info.get('webpage_url') or info.get('url'),
                'title': info.get('title', 'Unknown'),
                'thumbnail': info.get('thumbnail', ''),
                'duration': info.get('duration', 0),
                'requested_by': interaction.user
            }
            
            player.queue.append(song_data)
            
            embed = discord.Embed(
                title="✅ تمت الإضافة!",
                description=f"🎵 **{song_data['title']}**\n🔍 بحثت عن: {query}",
                color=Config.COLORS['success']
            )
            embed.add_field(name="📊 الموقع", value=f"#{len(player.queue)}")
            if song_data.get('thumbnail'):
                embed.set_thumbnail(url=song_data['thumbnail'])
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
            if not player.is_playing:
                # نمرر channel عشان play_next يقدر يبعت رسائل
                await player.play_next(self.channel, interaction.guild.voice_client)
        
        except Exception as e:
            await interaction.followup.send(f"❌ خطأ: {str(e)[:100]}", ephemeral=True)

class MusicPlayerView(discord.ui.View):
    """View لأمر !مشغل"""
    def __init__(self, cog, ctx):
        super().__init__(timeout=120)
        self.cog = cog
        self.ctx = ctx
    
    @discord.ui.button(label="🔍 ابحث عن أغنية", style=discord.ButtonStyle.primary, custom_id='open_search', emoji='🔍')
    async def search_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.voice:
            await interaction.response.send_message("❌ لازم تكون في قناة صوتية!", ephemeral=True)
            return
        
        modal = MusicSearchModal(self.cog, interaction.channel)
        await interaction.response.send_modal(modal)

class MusicPanelView(discord.ui.View):
    """لوحة التحكم الدائمة"""
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog
    
    async def _send(self, target, content=None, embed=None, ephemeral=False):
        if isinstance(target, discord.Interaction):
            if target.response.is_done():
                await target.followup.send(content=content, embed=embed, ephemeral=ephemeral)
            else:
                await target.response.send_message(content=content, embed=embed, ephemeral=ephemeral)
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not interaction.user.voice:
            await self._send(interaction, "❌ لازم تكون في قناة صوتية!", ephemeral=True)
            return False
        return True
    
    @discord.ui.button(label="🔍 بحث عن أغنية", style=discord.ButtonStyle.primary, custom_id='search', emoji='🔍')
    async def search_song(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = MusicSearchModal(self.cog, interaction.channel)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="⏯️ تشغيل/إيقاف", style=discord.ButtonStyle.secondary, custom_id='panel_play_pause', emoji='⏯️')
    async def panel_play_pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = self.cog.get_player(interaction.guild.id)
        
        if not interaction.guild.voice_client:
            await self._send(interaction, "❌ البوت مش في قناة صوتية!", ephemeral=True)
            return
        
        if interaction.guild.voice_client.is_playing():
            interaction.guild.voice_client.pause()
            player.is_paused = True
            await self._send(interaction, "⏸️ تم الإيقاف المؤقت")
        elif interaction.guild.voice_client.is_paused():
            interaction.guild.voice_client.resume()
            player.is_paused = False
            await self._send(interaction, "▶️ تم الاستكمال")
        else:
            if player.queue:
                await player.play_next(interaction.channel, interaction.guild.voice_client)
                await self._send(interaction, "▶️ تم التشغيل")
            else:
                await self._send(interaction, "❌ مفيش أغاني! اضغط 🔍 للبحث", ephemeral=True)
    
    @discord.ui.button(label="⏭️ تخطي", style=discord.ButtonStyle.secondary, custom_id='panel_skip', emoji='⏭️')
    async def panel_skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild.voice_client and interaction.guild.voice_client.is_playing():
            interaction.guild.voice_client.stop()
            await self._send(interaction, "⏭️ تم التخطي")
        else:
            await self._send(interaction, "❌ مفيش أغنية شغالة!", ephemeral=True)
    
    @discord.ui.button(label="📋 القائمة", style=discord.ButtonStyle.success, custom_id='panel_queue', emoji='📋')
    async def panel_queue(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = self.cog.get_player(interaction.guild.id)
        
        embed = discord.Embed(title="🎵 قائمة الأغاني", color=Config.COLORS['primary'])
        
        if player.current_song:
            embed.add_field(name="🎵 شغال دلوقتي", value=f"**{player.current_song['title']}**", inline=False)
        
        if player.queue:
            queue_text = ""
            for i, song in enumerate(player.queue[:10], 1):
                queue_text += f"{i}. **{song['title']}**\n"
            embed.add_field(name="📋 القائمة", value=queue_text, inline=False)
        
        if not player.current_song and not player.queue:
            embed.description = "❌ القائمة فاضية!"
        
        await self._send(interaction, embed=embed, ephemeral=True)
    
    @discord.ui.button(label="⏹️ إيقاف", style=discord.ButtonStyle.danger, custom_id='panel_stop', emoji='⏹️')
    async def panel_stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild.voice_client:
            player = self.cog.get_player(interaction.guild.id)
            player.queue.clear()
            player.history.clear()
            interaction.guild.voice_client.stop()
            await self._send(interaction, "⏹️ تم إيقاف كل حاجة")
        else:
            await self._send(interaction, "❌ البوت مش في قناة صوتية!", ephemeral=True)

class MusicPlayer:
    """مشغل الموسيقى"""
    def __init__(self):
        self.queue = []
        self.history = []
        self.current_song = None
        self.is_playing = False
        self.is_paused = False
    
    async def _send(self, destination, content=None, embed=None, view=None):
        """دالة إرسال ذكية - تتعامل مع Context, Interaction, Channel"""
        try:
            if isinstance(destination, commands.Context):
                await destination.send(content=content, embed=embed, view=view)
            elif isinstance(destination, discord.Interaction):
                if destination.response.is_done():
                    await destination.followup.send(content=content, embed=embed, view=view)
                else:
                    await destination.response.send_message(content=content, embed=embed, view=view)
            elif isinstance(destination, discord.TextChannel):
                await destination.send(content=content, embed=embed, view=view)
        except Exception as e:
            print(f"⚠️ خطأ في الإرسال: {e}")
    
    async def play_next(self, destination, voice_client):
        """تشغيل الأغنية التالية"""
        if self.queue:
            if self.current_song:
                self.history.append(self.current_song)
                if len(self.history) > 20:
                    self.history.pop(0)
            
            self.current_song = self.queue.pop(0)
            self.is_playing = True
            self.is_paused = False
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'quiet': True,
                'no_warnings': True,
            }
            
            try:
                print(f"🔍 جاري تحميل: {self.current_song['title']}")
                
                loop = asyncio.get_event_loop()
                info = await loop.run_in_executor(
                    None,
                    lambda: yt_dlp.YoutubeDL(ydl_opts).extract_info(self.current_song['url'], download=False)
                )
                
                if 'url' in info:
                    audio_url = info['url']
                else:
                    await self._send(destination, f"❌ مش لاقي رابط الصوت")
                    await self.play_next(destination, voice_client)
                    return
                
                print(f"✅ تم التحميل: {self.current_song['title']}")
                
                source = discord.FFmpegPCMAudio(
                    audio_url,
                    executable=FFMPEG_PATH,
                    before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                    options='-vn'
                )
                
                def after_play(error):
                    if error:
                        print(f"❌ خطأ بعد الأغنية: {error}")
                    coro = self.play_next(destination, voice_client)
                    # نحاول نحصل على loop
                    try:
                        loop = asyncio.get_event_loop()
                    except:
                        loop = None
                    
                    if loop and loop.is_running():
                        fut = asyncio.run_coroutine_threadsafe(coro, loop)
                        try:
                            fut.result()
                        except:
                            pass
                
                voice_client.play(source, after=after_play)
                
                embed = discord.Embed(
                    title="🎵 شغال دلوقتي",
                    description=f"**{self.current_song['title']}**",
                    color=Config.COLORS['primary']
                )
                embed.add_field(name="👤 بواسطة", value=self.current_song['requested_by'].mention)
                if self.current_song.get('thumbnail'):
                    embed.set_thumbnail(url=self.current_song['thumbnail'])
                embed.set_footer(text="استخدم الأزرار للتحكم")
                
                view = MusicControlView(self, destination)
                await self._send(destination, embed=embed, view=view)
                
            except Exception as e:
                print(f"❌ خطأ في التشغيل: {e}")
                await self._send(destination, f"❌ حصل خطأ: {str(e)[:100]}")
                await self.play_next(destination, voice_client)
        else:
            self.is_playing = False
            self.current_song = None

class Music(commands.Cog, name="🎵 الموسيقى"):
    """نظام الموسيقى"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.players = {}
    
    def get_player(self, guild_id):
        if guild_id not in self.players:
            self.players[guild_id] = MusicPlayer()
        return self.players[guild_id]
    
    @commands.command(name='مشغل', aliases=['player', 'شغل_نافذة', 'بحث'])
    async def music_player(self, ctx: commands.Context):
        """فتح نافذة البحث عن أغنية"""
        if not ctx.author.voice:
            await ctx.send("❌ لازم تكون في قناة صوتية!")
            return
        
        embed = discord.Embed(
            title="🎵 مشغل الموسيقى",
            description=(
                "اضغط على الزرار عشان تفتح نافذة البحث\n"
                "واكتب اسم الأغنية اللي عايزها!"
            ),
            color=Config.COLORS['primary']
        )
        
        view = MusicPlayerView(self, ctx)
        await ctx.send(embed=embed, view=view)
    
    @commands.command(name='قناة_موسيقى', aliases=['music_channel', 'قناة_الاغاني'])
    @commands.has_permissions(manage_channels=True)
    async def music_channel(self, ctx: commands.Context):
        """إنشاء قناة موسيقى دائمة"""
        existing = discord.utils.get(ctx.guild.channels, name="🎵-الموسيقى")
        if existing:
            await ctx.send(f"❌ القناة موجودة بالفعل: {existing.mention}")
            return
        
        await ctx.send("🔄 جاري إنشاء قناة الموسيقى...")
        
        try:
            category = discord.utils.get(ctx.guild.categories, name="🎵 الموسيقى")
            if not category:
                category = await ctx.guild.create_category("🎵 الموسيقى")
            
            text_channel = await ctx.guild.create_text_channel(
                "🎵-الموسيقى",
                category=category,
                topic="🎵 قناة الموسيقى - استخدم الأزرار للتحكم"
            )
            
            voice_channel = await ctx.guild.create_voice_channel(
                "🎵 استمع",
                category=category
            )
            
            from database import db
            await db.execute(
                'INSERT OR REPLACE INTO music_channels (guild_id, text_channel_id, voice_channel_id) VALUES (?, ?, ?)',
                (ctx.guild.id, text_channel.id, voice_channel.id)
            )
            
            embed = discord.Embed(
                title="🎵 قناة الموسيقى",
                description=(
                    "**مرحبًا بك في قناة الموسيقى!** 🎶\n\n"
                    "**🎯 طريقة الاستخدام:**\n"
                    "• اضغط 🔍 **بحث عن أغنية** واكتب اسم الأغنية\n"
                    "• استخدم الأزرار للتحكم في التشغيل\n"
                    "• ادخل قناة **🎵 استمع** الصوتية للاستماع\n\n"
                    "**📋 الأوامر المتاحة:**\n"
                    "!مشغل - فتح نافذة البحث\n"
                    "!قائمة - عرض قائمة الأغاني\n"
                    "!اطلع - خروج البوت\n"
                ),
                color=Config.COLORS['primary']
            )
            
            view = MusicPanelView(self)
            await text_channel.send(embed=embed, view=view)
            
            welcome_embed = discord.Embed(
                title="🎉 جاهز!",
                description=(
                    f"✅ تم إنشاء:\n"
                    f"• {text_channel.mention} - للتحكم\n"
                    f"• {voice_channel.mention} - للاستماع\n\n"
                    f"**ادخل القناة الصوتية وجرب!** 🎵"
                ),
                color=Config.COLORS['success']
            )
            await ctx.send(embed=welcome_embed)
            
        except Exception as e:
            await ctx.send(f"❌ خطأ: {str(e)}")
    
    @commands.command(name='انشاء_قناة_صوتية', aliases=['createvoice', 'قناة_صوتية'])
    @commands.has_permissions(manage_channels=True)
    async def create_voice_channel(self, ctx: commands.Context, *, name: str = "🎵 الموسيقى"):
        try:
            channel = await ctx.guild.create_voice_channel(name)
            embed = discord.Embed(
                title="✅ تم إنشاء القناة!",
                description=f"🎤 {channel.mention} جاهزة!",
                color=Config.COLORS['success']
            )
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ خطأ: {str(e)}")
    
    @commands.command(name='انضم', aliases=['join_voice', 'دخول_صوت'])
    async def join(self, ctx: commands.Context):
        if not ctx.author.voice:
            await ctx.send("❌ لازم تكون في قناة صوتية!")
            return
        
        channel = ctx.author.voice.channel
        
        try:
            if ctx.voice_client and ctx.voice_client.is_connected():
                await ctx.voice_client.move_to(channel)
            else:
                await channel.connect()
            
            embed = discord.Embed(
                title="✅ دخلت القناة!",
                description=f"🎤 أنا دلوقتي في {channel.mention}",
                color=Config.COLORS['success']
            )
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ خطأ في الاتصال: {str(e)[:100]}")
    
    @commands.command(name='اطلع', aliases=['disconnect', 'خروج_صوت'])
    async def leave(self, ctx: commands.Context):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            player = self.get_player(ctx.guild.id)
            player.queue.clear()
            player.history.clear()
            player.current_song = None
            player.is_playing = False
            
            embed = discord.Embed(
                title="✅ طلعت!",
                description="👋 البوت طلع من القناة",
                color=Config.COLORS['success']
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ أنا مش في قناة صوتية!")
    
    @commands.command(name='شغل_اغنية', aliases=['play', 'p', 'اغنية'])
    async def play(self, ctx: commands.Context, *, query: str):
        if not ctx.author.voice:
            await ctx.send("❌ لازم تكون في قناة صوتية!")
            return
        
        if not ctx.voice_client or not ctx.voice_client.is_connected():
            await ctx.invoke(self.join)
            await asyncio.sleep(1)
        
        if not ctx.voice_client:
            await ctx.send("❌ فشل الاتصال!")
            return
        
        player = self.get_player(ctx.guild.id)
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
        }
        
        status_msg = await ctx.send(f"🔍 جاري البحث عن: **{query}**...")
        
        try:
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(
                None,
                lambda: yt_dlp.YoutubeDL(ydl_opts).extract_info(f"ytsearch:1 {query}", download=False)
            )
            
            if 'entries' in info and info['entries']:
                info = info['entries'][0]
            
            song_data = {
                'url': info.get('webpage_url') or info.get('url'),
                'title': info.get('title', 'Unknown'),
                'thumbnail': info.get('thumbnail', ''),
                'duration': info.get('duration', 0),
                'requested_by': ctx.author
            }
            
            player.queue.append(song_data)
            
            embed = discord.Embed(
                title="✅ تمت الإضافة!",
                description=f"🎵 **{song_data['title']}**",
                color=Config.COLORS['success']
            )
            embed.add_field(name="📊 الموقع", value=f"#{len(player.queue)}")
            if song_data.get('thumbnail'):
                embed.set_thumbnail(url=song_data['thumbnail'])
            
            await status_msg.edit(embed=embed)
            
            if not player.is_playing:
                await player.play_next(ctx, ctx.voice_client)
        
        except Exception as e:
            await status_msg.edit(content=f"❌ خطأ: {str(e)[:100]}")
    
    @commands.command(name='وقف_اغنية', aliases=['pause', 'وقف_مؤقت'])
    async def pause(self, ctx: commands.Context):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            self.get_player(ctx.guild.id).is_paused = True
            await ctx.send("⏸️ تم الإيقاف المؤقت")
        else:
            await ctx.send("❌ مفيش أغنية شغالة!")
    
    @commands.command(name='كمل_اغنية', aliases=['resume', 'كمل_تشغيل'])
    async def resume(self, ctx: commands.Context):
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            self.get_player(ctx.guild.id).is_paused = False
            await ctx.send("▶️ تم الاستكمال")
        else:
            await ctx.send("❌ مفيش أغنية متوقفة!")
    
    @commands.command(name='تخطي_اغنية', aliases=['skip', 'تخطي'])
    async def skip(self, ctx: commands.Context):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("⏭️ تم التخطي")
        else:
            await ctx.send("❌ مفيش أغنية شغالة!")
    
    @commands.command(name='ايقاف_اغنية', aliases=['stop', 'ايقاف'])
    async def stop(self, ctx: commands.Context):
        if ctx.voice_client:
            player = self.get_player(ctx.guild.id)
            player.queue.clear()
            player.history.clear()
            ctx.voice_client.stop()
            await ctx.send("🛑 تم إيقاف كل حاجة")
        else:
            await ctx.send("❌ أنا مش في قناة صوتية!")
    
    @commands.command(name='قائمة', aliases=['queue', 'قائمة_الاغاني'])
    async def queue(self, ctx: commands.Context):
        player = self.get_player(ctx.guild.id)
        
        if not player.queue and not player.current_song:
            await ctx.send("❌ القائمة فاضية!")
            return
        
        embed = discord.Embed(title="🎵 قائمة الأغاني", color=Config.COLORS['primary'])
        
        if player.current_song:
            embed.add_field(name="🎵 شغال دلوقتي", value=f"**{player.current_song['title']}**", inline=False)
        
        if player.queue:
            queue_text = ""
            for i, song in enumerate(player.queue[:10], 1):
                queue_text += f"{i}. **{song['title']}**\n"
            if len(player.queue) > 10:
                queue_text += f"\n... و {len(player.queue) - 10} أغنية تانية"
            embed.add_field(name="📋 القائمة", value=queue_text, inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='now_playing', aliases=['الان', 'np'])
    async def now_playing(self, ctx: commands.Context):
        player = self.get_player(ctx.guild.id)
        
        if not player.current_song:
            await ctx.send("❌ مفيش أغنية شغالة!")
            return
        
        embed = discord.Embed(
            title="🎵 شغال دلوقتي",
            description=f"**{player.current_song['title']}**",
            color=Config.COLORS['primary']
        )
        embed.add_field(name="👤 طلب بواسطة", value=player.current_song['requested_by'].mention)
        if player.current_song.get('thumbnail'):
            embed.set_thumbnail(url=player.current_song['thumbnail'])
        
        view = MusicControlView(player, ctx)
        await ctx.send(embed=embed, view=view)
    
    @commands.command(name='التاريخ', aliases=['history', 'سابقة'])
    async def history(self, ctx: commands.Context):
        player = self.get_player(ctx.guild.id)
        
        if not player.history:
            await ctx.send("❌ مفيش أغاني في التاريخ!")
            return
        
        embed = discord.Embed(title="📜 تاريخ الأغاني", color=Config.COLORS['primary'])
        
        history_text = ""
        for i, song in enumerate(reversed(player.history[-10:]), 1):
            history_text += f"{i}. **{song['title']}**\n"
        
        embed.add_field(name="🎵 آخر 10 أغاني", value=history_text, inline=False)
        await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    from database import db
    await db.execute('''
        CREATE TABLE IF NOT EXISTS music_channels (
            guild_id INTEGER PRIMARY KEY,
            text_channel_id INTEGER,
            voice_channel_id INTEGER
        )
    ''')
    
    await bot.add_cog(Music(bot))