import discord
from discord.ext import commands
import random
from typing import Optional, List
from config import Config

class TicTacToeButton(discord.ui.Button['TicTacToe']):
    """زرار في لعبة X O"""
    def __init__(self, x: int, y: int):
        super().__init__(style=discord.ButtonStyle.secondary, label='\u200b', row=y)
        self.x = x
        self.y = y
    
    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        view: TicTacToe = self.view
        state = view.board[self.y][self.x]
        
        if state in (view.X, view.O):
            await interaction.response.send_message("الخانة دي مأخوذة!", ephemeral=True)
            return
        
        if interaction.user.id != view.current_player.id:
            await interaction.response.send_message("مش دورك!", ephemeral=True)
            return
        
        if view.current_player.id == view.player1.id:
            self.style = discord.ButtonStyle.danger
            self.label = 'X'
            self.emoji = '❌'
            view.board[self.y][self.x] = view.X
            view.current_player = view.player2
        else:
            self.style = discord.ButtonStyle.primary
            self.label = 'O'
            self.emoji = '⭕'
            view.board[self.y][self.x] = view.O
            view.current_player = view.player1
        
        self.disabled = True
        
        winner = view.check_winner()
        if winner:
            view.stop()
            await interaction.response.edit_message(content=f"🎉 {winner.mention} كسب!", view=view)
        elif view.check_tie():
            view.stop()
            await interaction.response.edit_message(content="🤝 تعادل!", view=view)
        else:
            await interaction.response.edit_message(
                content=f"دور {view.current_player.mention} ({'❌' if view.current_player.id == view.player1.id else '⭕'})",
                view=view
            )

class TicTacToe(discord.ui.View):
    """لعبة X O"""
    children: List[TicTacToeButton]
    X = -1
    O = 1
    TIE = 2
    
    def __init__(self, player1: discord.Member, player2: discord.Member):
        super().__init__(timeout=180)
        self.player1 = player1
        self.player2 = player2
        self.current_player = player1
        self.board = [[0 for _ in range(3)] for _ in range(3)]
        
        for y in range(3):
            for x in range(3):
                self.add_item(TicTacToeButton(x, y))
    
    def check_winner(self) -> Optional[discord.Member]:
        for row in self.board:
            if sum(row) == 3: return self.player2
            if sum(row) == -3: return self.player1
        
        for col in range(3):
            col_sum = sum(self.board[row][col] for row in range(3))
            if col_sum == 3: return self.player2
            if col_sum == -3: return self.player1
        
        diag1 = sum(self.board[i][i] for i in range(3))
        diag2 = sum(self.board[i][2-i] for i in range(3))
        
        if diag1 == 3 or diag2 == 3: return self.player2
        if diag1 == -3 or diag2 == -3: return self.player1
        
        return None
    
    def check_tie(self) -> bool:
        return all(self.board[y][x] != 0 for y in range(3) for x in range(3))

class ConnectFourButton(discord.ui.Button['ConnectFour']):
    """زرار في لعبة Connect 4"""
    def __init__(self, x: int, y: int):
        super().__init__(style=discord.ButtonStyle.secondary, label='\u200b', row=y)
        self.x = x
        self.y = y

class ConnectFour(discord.ui.View):
    """لعبة Connect 4"""
    def __init__(self, player1: discord.Member, player2: discord.Member):
        super().__init__(timeout=180)
        self.player1 = player1
        self.player2 = player2
        self.current_player = player1
        self.board = [[0 for _ in range(7)] for _ in range(6)]
        
        for y in range(6):
            for x in range(7):
                self.add_item(ConnectFourButton(x, y))

class Games(commands.Cog, name="🎮 الألعاب"):
    """ألعاب تفاعلية"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.command(name='xo', aliases=['tictactoe', 'اكس_او'])
    async def tic_tac_toe(self, ctx: commands.Context, opponent: discord.Member = None):
        """لعبة X O"""
        if opponent is None:
            await ctx.send("❌ لازم تحدد خصمك! مثال: `!xo @شخص`")
            return
        
        if opponent.bot:
            await ctx.send("❌ مش ممكن تلعب مع بوت!")
            return
        
        if opponent == ctx.author:
            await ctx.send("❌ مش ممكن تلعب مع نفسك!")
            return
        
        # تأكيد من الخصم
        class AcceptView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=30)
                self.value = None
            
            @discord.ui.button(label="✅ قبول", style=discord.ButtonStyle.success)
            async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user.id != opponent.id:
                    await interaction.response.send_message("ده مش دورك!", ephemeral=True)
                    return
                self.value = True
                self.stop()
            
            @discord.ui.button(label="❌ رفض", style=discord.ButtonStyle.danger)
            async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user.id != opponent.id:
                    await interaction.response.send_message("ده مش دورك!", ephemeral=True)
                    return
                self.value = False
                self.stop()
        
        view = AcceptView()
        msg = await ctx.send(
            f"{opponent.mention}، {ctx.author.mention} بيتحداك في X O! ⭕❌",
            view=view
        )
        
        await view.wait()
        
        if view.value is None:
            await msg.edit(content="⏰ انتهى الوقت! ما فيش رد.", view=None)
            return
        
        if not view.value:
            await msg.edit(content="❌ رفض التحدي!", view=None)
            return
        
        # بدء اللعبة
        game_view = TicTacToe(ctx.author, opponent)
        await msg.edit(
            content=f"دور {ctx.author.mention} (❌)",
            view=game_view
        )
    
    @commands.command(name='روليت', aliases=['roulette'])
    async def roulette(self, ctx: commands.Context, bet: int = 100, color: str = None):
        """لعبة الروليت"""
        if bet <= 0:
            await ctx.send("❌ الرهان لازم يكون أكبر من 0!")
            return
        
        from database import db
        data = await db.get_user_economy(ctx.author.id)
        if data['balance'] < bet:
            await ctx.send("❌ معاكش فلوس كفاية!")
            return
        
        if color and color.lower() not in ['red', 'أحمر', 'black', 'أسود', 'green', 'أخضر']:
            await ctx.send("❌ اللون لازم يكون: أحمر، أسود، أو أخضر")
            return
        
        # الروليت
        numbers = list(range(0, 37))
        result = random.choice(numbers)
        
        # تحديد اللون
        red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
        if result == 0:
            result_color = "🟢 أخضر"
        elif result in red_numbers:
            result_color = "🔴 أحمر"
        else:
            result_color = "⚫ أسود"
        
        # حساب الربح
        winnings = 0
        if color:
            color_lower = color.lower()
            if color_lower in ['red', 'أحمر'] and result in red_numbers:
                winnings = bet * 2
            elif color_lower in ['black', 'أسود'] and result not in red_numbers and result != 0:
                winnings = bet * 2
            elif color_lower in ['green', 'أخضر'] and result == 0:
                winnings = bet * 35
        else:
            # رهان عشوائي
            if result != 0:
                winnings = bet * 2 if random.random() < 0.5 else 0
        
        await db.update_balance(ctx.author.id, winnings - bet)
        
        embed = discord.Embed(
            title="🎰 الروليت",
            color=Config.COLORS['primary']
        )
        embed.add_field(name="🎯 الرقم", value=f"**{result}**", inline=True)
        embed.add_field(name="🎨 اللون", value=result_color, inline=True)
        embed.add_field(name="💰 الرهان", value=f"{bet:,} جنيه", inline=True)
        
        if winnings > 0:
            embed.add_field(name="🎉 النتيجة", value=f"ربحت **{winnings:,}** جنيه!", inline=False)
        else:
            embed.add_field(name="😔 النتيجة", value=f"خسرت **{bet:,}** جنيه", inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='لعبة_حظ', aliases=['luck', 'حظي'])
    async def luck_game(self, ctx: commands.Context):
        """لعبة الحظ"""
        outcomes = [
            ("🎉 Jackpot! ربحت 1000 جنيه!", 1000),
            ("✨ ربحت 500 جنيه!", 500),
            ("💫 ربحت 200 جنيه!", 200),
            ("🎊 ربحت 100 جنيه!", 100),
            ("😔 خسرت 50 جنيه", -50),
            ("💀 خسرت 100 جنيه", -100),
            ("🍀 محظوظ! ربحت 300 جنيه!", 300),
        ]
        
        text, amount = random.choice(outcomes)
        
        from database import db
        await db.update_balance(ctx.author.id, amount)
        
        embed = discord.Embed(
            title="🎲 لعبة الحظ",
            description=text,
            color=Config.COLORS['success'] if amount > 0 else Config.COLORS['error']
        )
        
        data = await db.get_user_economy(ctx.author.id)
        embed.add_field(name="💵 رصيدك", value=f"{data['balance']:,} جنيه")
        
        await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Games(bot))