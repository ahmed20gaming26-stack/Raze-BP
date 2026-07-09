import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # معلومات البوت
    TOKEN = os.getenv('DISCORD_TOKEN')
    PREFIX = ['!', '؟', 'يا بوت ', 'بوت ']
    OWNER_IDS = [int(x) for x in os.getenv('OWNER_IDS', '').split(',') if x.strip()]
    
    # الألوان
    COLORS = {
        'primary': 0xFFD700,      # ذهبي
        'success': 0x00FF00,      # أخضر
        'error': 0xFF0000,        # أحمر
        'warning': 0xFFA500,      # برتقالي
        'info': 0x0099FF,         # أزرق
        'purple': 0x9B59B6,       # بنفسجي
    }
    
    # إعدادات الاقتصاد
    ECONOMY = {
        'daily_min': 100,
        'daily_max': 500,
        'work_min': 50,
        'work_max': 300,
        'work_cooldown': 3600,
        'daily_cooldown': 86400,
        'crime_chance': 0.3,
        'rob_chance': 0.4,
    }
    
    # إعدادات المستويات
    LEVELS = {
        'xp_min': 15,
        'xp_max': 35,
        'cooldown': 60,
        'base_xp': 100,
        'multiplier': 1.5,
    }
    
    # إعدادات مكافحة السبام
    ANTI_SPAM = {
        'messages_limit': 5,
        'time_window': 7,
        'mentions_limit': 5,
        'caps_threshold': 0.7,
    }
    
    # روابط
    IMAGES = {
        'welcome_bg': 'assets/welcome_bg.png',
        'rank_bg': 'assets/rank_bg.png',
    }