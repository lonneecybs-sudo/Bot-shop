from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

# ТВОИ ДАННЫЕ
TOKEN = "8546103501:AAGZv9evkjpQJR92TxX5-6Do7W_7M6XwXbw"
ADMIN_ID = 8259326703
ADMIN_PASSWORD = "17157150Sw!"

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Тарифы
class Tariff(Enum):
    MIN = ("⭐ Минимальный", 50)
    MID = ("⭐⭐ Средний", 100)
    MAX = ("⭐⭐⭐ Полный", 300)

# Класс заказа
@dataclass
class Order:
    id: int
    user_id: int
    username: str
    tariff: Tariff
    description: str
    status: str  # pending, waiting_payment, development, completed
    created_at: datetime
    paid: bool = False
    token: str = None

# Класс отзыва
@dataclass
class Review:
    id: int
    user_id: int
    username: str
    rating: int  # 1-5
    text: str
    date: datetime
    approved: bool = False

# Глобальные хранилища
orders: Dict[int, Order] = {}
order_counter = 0
reviews: List[Review] = []
review_counter = 0

# Текст главного меню
MAIN_MENU_TEXT = (
    "✨ <b>Добро пожаловать в премиум студию разработки ботов!</b>\n\n"
    "🎯 <b>Почему выбирают нас:</b>\n"
    "✅ Индивидуальный подход\n"
    "✅ Быстрая разработка (1-5 дней)\n"
    "✅ Полное сопровождение\n"
    "✅ Гарантия качества\n\n"
    
    "🔥 <b>Тарифы:</b>\n"
    "┌─────────────────────────┐\n"
    "│ ⭐ МИНИМАЛЬНЫЙ • 50⭐    │\n"
    "│ Базовые команды          │\n"
    "├─────────────────────────┤\n"
    "│ ⭐⭐ СРЕДНИЙ • 100⭐     │\n"
    "│ Команды + инлайн кнопки  │\n"
    "├─────────────────────────┤\n"
    "│ ⭐⭐⭐ ПОЛНЫЙ • 300⭐     │\n"
    "│ Любые функции, кастом    │\n"
    "└─────────────────────────┘"
)
