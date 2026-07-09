import aiosqlite
import os
import time
from typing import Optional, Any

class Database:
    def __init__(self, db_path: str = 'data/bot.db'):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db: Optional[aiosqlite.Connection] = None
    
    async def connect(self):
        """الاتصال بقاعدة البيانات"""
        self.db = await aiosqlite.connect(self.db_path)
        await self.db.execute("PRAGMA journal_mode=WAL")
        await self.create_tables()
    
    async def close(self):
        """إغلاق الاتصال"""
        if self.db:
            await self.db.close()
    
    async def create_tables(self):
        """إنشاء الجداول"""
        await self.db.executescript('''
            -- جدول الاقتصاد
            CREATE TABLE IF NOT EXISTS economy (
                user_id INTEGER PRIMARY KEY,
                balance INTEGER DEFAULT 0,
                bank INTEGER DEFAULT 0,
                last_daily INTEGER DEFAULT 0,
                last_work INTEGER DEFAULT 0,
                last_crime INTEGER DEFAULT 0,
                total_earned INTEGER DEFAULT 0,
                total_spent INTEGER DEFAULT 0,
                inventory TEXT DEFAULT '{}'
            );
            
            -- جدول المستويات
            CREATE TABLE IF NOT EXISTS levels (
                user_id INTEGER PRIMARY KEY,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                total_messages INTEGER DEFAULT 0,
                last_xp INTEGER DEFAULT 0,
                background TEXT DEFAULT 'default'
            );
            
            -- جدول التحذيرات
            CREATE TABLE IF NOT EXISTS warns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                user_id INTEGER,
                moderator_id INTEGER,
                reason TEXT,
                timestamp INTEGER
            );
            
            -- جدول التذاكر
            CREATE TABLE IF NOT EXISTS tickets (
                channel_id INTEGER PRIMARY KEY,
                guild_id INTEGER,
                user_id INTEGER,
                status TEXT DEFAULT 'open',
                created_at INTEGER,
                closed_at INTEGER,
                closed_by INTEGER
            );
            
            -- جدول المسابقات
            CREATE TABLE IF NOT EXISTS giveaways (
                message_id INTEGER PRIMARY KEY,
                guild_id INTEGER,
                channel_id INTEGER,
                host_id INTEGER,
                prize TEXT,
                winners_count INTEGER,
                end_time INTEGER,
                requirements TEXT DEFAULT '{}'
            );
            
            -- جدول التذكيرات
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                channel_id INTEGER,
                message TEXT,
                remind_time INTEGER,
                created_at INTEGER
            );
            
            -- جدول الاقتراحات
            CREATE TABLE IF NOT EXISTS suggestions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                user_id INTEGER,
                message_id INTEGER,
                content TEXT,
                status TEXT DEFAULT 'pending',
                created_at INTEGER
            );
            
            -- جدول السجلات
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                event_type TEXT,
                user_id INTEGER,
                target_id INTEGER,
                details TEXT,
                timestamp INTEGER
            );
            
            -- جدول إعدادات السيرفرات
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id INTEGER PRIMARY KEY,
                prefix TEXT DEFAULT '!',
                welcome_channel INTEGER,
                goodbye_channel INTEGER,
                logs_channel INTEGER,
                suggestions_channel INTEGER,
                welcome_message TEXT,
                goodbye_message TEXT,
                autorole_id INTEGER,
                leveling_enabled INTEGER DEFAULT 1,
                economy_enabled INTEGER DEFAULT 1,
                anti_spam_enabled INTEGER DEFAULT 1
            );
            
            -- جدول AFK
            CREATE TABLE IF NOT EXISTS afk (
                user_id INTEGER PRIMARY KEY,
                guild_id INTEGER,
                reason TEXT,
                timestamp INTEGER
            );
            
            -- جدول المتجر
            CREATE TABLE IF NOT EXISTS shop_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                name TEXT,
                description TEXT,
                price INTEGER,
                role_id INTEGER,
                stock INTEGER DEFAULT -1
            );
            
            -- جدول الملاحظات
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                content TEXT,
                created_at INTEGER
            );
            
            -- جدول قائمة المهام
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                content TEXT,
                completed INTEGER DEFAULT 0,
                created_at INTEGER
            );
            
            -- جدول إعطاء الرتب بالريأكشن
            CREATE TABLE IF NOT EXISTS reaction_roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                message_id INTEGER,
                emoji TEXT,
                role_id INTEGER,
                UNIQUE(message_id, emoji)
            );
        ''')
        await self.db.commit()
    
    # ===== دوال الاقتصاد =====
    async def get_user_economy(self, user_id: int) -> dict:
        async with self.db.execute(
            'SELECT * FROM economy WHERE user_id = ?', (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                await self.db.execute(
                    'INSERT INTO economy (user_id) VALUES (?)', (user_id,)
                )
                await self.db.commit()
                return {
                    'user_id': user_id, 'balance': 0, 'bank': 0,
                    'last_daily': 0, 'last_work': 0, 'last_crime': 0,
                    'total_earned': 0, 'total_spent': 0, 'inventory': '{}'
                }
            columns = [col[0] for col in cursor.description]
            return dict(zip(columns, row))
    
    async def update_balance(self, user_id: int, amount: int):
        await self.db.execute(
            'UPDATE economy SET balance = balance + ? WHERE user_id = ?',
            (amount, user_id)
        )
        if amount > 0:
            await self.db.execute(
                'UPDATE economy SET total_earned = total_earned + ? WHERE user_id = ?',
                (amount, user_id)
            )
        else:
            await self.db.execute(
                'UPDATE economy SET total_spent = total_spent + ? WHERE user_id = ?',
                (abs(amount), user_id)
            )
        await self.db.commit()
    
    # ===== دوال المستويات =====
    async def get_user_level(self, user_id: int) -> dict:
        async with self.db.execute(
            'SELECT * FROM levels WHERE user_id = ?', (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                await self.db.execute(
                    'INSERT INTO levels (user_id) VALUES (?)', (user_id,)
                )
                await self.db.commit()
                return {'user_id': user_id, 'xp': 0, 'level': 1, 'total_messages': 0, 'last_xp': 0}
            columns = [col[0] for col in cursor.description]
            return dict(zip(columns, row))
    
    async def add_xp(self, user_id: int, xp: int) -> tuple:
        """إضافة XP وإرجاع (المستوى_القديم, المستوى_الجديد)"""
        user = await self.get_user_level(user_id)
        old_level = user['level']
        
        new_xp = user['xp'] + xp
        new_level = user['level']
        new_messages = user['total_messages'] + 1
        
        # حساب المستوى الجديد
        required_xp = 5 * (new_level ** 2) + 50 * new_level + 100
        while new_xp >= required_xp:
            new_xp -= required_xp
            new_level += 1
            required_xp = 5 * (new_level ** 2) + 50 * new_level + 100
        
        await self.db.execute(
            'UPDATE levels SET xp = ?, level = ?, total_messages = ?, last_xp = ? WHERE user_id = ?',
            (new_xp, new_level, new_messages, int(time.time()), user_id)
        )
        await self.db.commit()
        return old_level, new_level
    
    async def get_leaderboard(self, limit: int = 10) -> list:
        async with self.db.execute(
            'SELECT user_id, level, xp, total_messages FROM levels ORDER BY level DESC, xp DESC LIMIT ?',
            (limit,)
        ) as cursor:
            return await cursor.fetchall()
    
    # ===== دوال التحذيرات =====
    async def add_warn(self, guild_id: int, user_id: int, mod_id: int, reason: str) -> int:
        await self.db.execute(
            'INSERT INTO warns (guild_id, user_id, moderator_id, reason, timestamp) VALUES (?, ?, ?, ?, ?)',
            (guild_id, user_id, mod_id, reason, int(time.time()))
        )
        await self.db.commit()
        async with self.db.execute('SELECT last_insert_rowid()') as cursor:
            return (await cursor.fetchone())[0]
    
    async def get_warns(self, guild_id: int, user_id: int) -> list:
        async with self.db.execute(
            'SELECT * FROM warns WHERE guild_id = ? AND user_id = ? ORDER BY timestamp DESC',
            (guild_id, user_id)
        ) as cursor:
            rows = await cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
    
    async def clear_warns(self, guild_id: int, user_id: int):
        await self.db.execute(
            'DELETE FROM warns WHERE guild_id = ? AND user_id = ?',
            (guild_id, user_id)
        )
        await self.db.commit()
    
    # ===== دوال الإعدادات =====
    async def get_guild_settings(self, guild_id: int) -> dict:
        async with self.db.execute(
            'SELECT * FROM guild_settings WHERE guild_id = ?', (guild_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                await self.db.execute(
                    'INSERT INTO guild_settings (guild_id) VALUES (?)', (guild_id,)
                )
                await self.db.commit()
                return {'guild_id': guild_id}
            columns = [col[0] for col in cursor.description]
            return dict(zip(columns, row))
    
    async def update_guild_setting(self, guild_id: int, key: str, value: Any):
        await self.db.execute(
            f'UPDATE guild_settings SET {key} = ? WHERE guild_id = ?',
            (value, guild_id)
        )
        await self.db.commit()
    
    # ===== دوال عامة =====
    async def execute(self, query: str, params: tuple = ()):
        await self.db.execute(query, params)
        await self.db.commit()
    
    async def fetch(self, query: str, params: tuple = ()):
        async with self.db.execute(query, params) as cursor:
            return await cursor.fetchall()

# إنشاء نسخة عامة
db = Database()