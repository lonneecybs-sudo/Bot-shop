import sqlite3
from typing import List, Dict, Optional
from datetime import datetime

# ========== БАЗА ДАННЫХ ==========

def get_db_connection():
    """Создание соединения с БД"""
    conn = sqlite3.connect('shop_bot.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Инициализация таблиц базы данных"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Таблица пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Таблица товаров
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            category TEXT,
            in_stock INTEGER DEFAULT 1
        )
    ''')
    
    # Таблица заказов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER DEFAULT 1,
            total_price REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')
    
    # Таблица отзывов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            rating INTEGER CHECK(rating >= 1 AND rating <= 5),
            comment TEXT,
            status TEXT DEFAULT 'pending',  -- 'pending', 'approved', 'rejected'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            moderated_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (order_id) REFERENCES orders(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')
    
    # Добавление тестовых товаров, если таблица пуста
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        sample_products = [
            ('Смартфон X', 'Новейший смартфон с отличной камерой', 59999.99, 'Электроника'),
            ('Ноутбук Pro', 'Мощный ноутбук для работы и игр', 89999.99, 'Электроника'),
            ('Наушники', 'Беспроводные наушники с шумоподавлением', 5999.99, 'Аксессуары'),
            ('Клавиатура', 'Механическая игровая клавиатура', 4999.99, 'Аксессуары'),
            ('Мышка', 'Беспроводная игровая мышь', 2999.99, 'Аксессуары')
        ]
        cursor.executemany(
            "INSERT INTO products (name, description, price, category) VALUES (?, ?, ?, ?)",
            sample_products
        )
    
    conn.commit()
    conn.close()

# ========== РАБОТА С ПОЛЬЗОВАТЕЛЯМИ ==========

def add_user(user_id: int, username: str = None, first_name: str = None):
    """Добавление нового пользователя"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
        (user_id, username, first_name)
    )
    conn.commit()
    conn.close()

def get_user(user_id: int):
    """Получение информации о пользователе"""
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    return user

# ========== РАБОТА С ТОВАРАМИ ==========

def get_products(category: str = None):
    """Получение списка товаров (опционально по категории)"""
    conn = get_db_connection()
    if category:
        products = conn.execute(
            "SELECT * FROM products WHERE in_stock = 1 AND category = ?",
            (category,)
        ).fetchall()
    else:
        products = conn.execute("SELECT * FROM products WHERE in_stock = 1").fetchall()
    conn.close()
    return products

def get_product(product_id: int):
    """Получение товара по ID"""
    conn = get_db_connection()
    product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    conn.close()
    return product

def get_categories():
    """Получение списка категорий"""
    conn = get_db_connection()
    categories = conn.execute("SELECT DISTINCT category FROM products WHERE in_stock = 1").fetchall()
    conn.close()
    return [cat['category'] for cat in categories]

# ========== РАБОТА С ЗАКАЗАМИ ==========

def create_order(user_id: int, product_id: int, quantity: int = 1):
    """Создание нового заказа"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Получаем цену товара
    product = get_product(product_id)
    if not product:
        conn.close()
        return None
    
    total_price = product['price'] * quantity
    
    cursor.execute(
        """INSERT INTO orders (user_id, product_id, quantity, total_price) 
           VALUES (?, ?, ?, ?)""",
        (user_id, product_id, quantity, total_price)
    )
    order_id = cursor.lastrowid
    
    conn.commit()
    conn.close()
    return order_id

def get_user_orders(user_id: int):
    """Получение заказов пользователя"""
    conn = get_db_connection()
    orders = conn.execute(
        """SELECT o.*, p.name as product_name 
           FROM orders o 
           JOIN products p ON o.product_id = p.id 
           WHERE o.user_id = ? 
           ORDER BY o.order_date DESC""",
        (user_id,)
    ).fetchall()
    conn.close()
    return orders

def get_order(order_id: int):
    """Получение заказа по ID"""
    conn = get_db_connection()
    order = conn.execute(
        """SELECT o.*, p.name as product_name, p.description 
           FROM orders o 
           JOIN products p ON o.product_id = p.id 
           WHERE o.id = ?""",
        (order_id,)
    ).fetchone()
    conn.close()
    return order

def update_order_status(order_id: int, status: str):
    """Обновление статуса заказа"""
    conn = get_db_connection()
    conn.execute(
        "UPDATE orders SET status = ? WHERE id = ?",
        (status, order_id)
    )
    conn.commit()
    conn.close()

# ========== РАБОТА С ОТЗЫВАМИ ==========

def create_review(user_id: int, order_id: int, product_id: int, rating: int, comment: str = None):
    """Создание нового отзыва"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Проверяем, не оставлял ли пользователь уже отзыв на этот заказ
    existing = cursor.execute(
        "SELECT id FROM reviews WHERE user_id = ? AND order_id = ?",
        (user_id, order_id)
    ).fetchone()
    
    if existing:
        conn.close()
        return None
    
    cursor.execute(
        """INSERT INTO reviews (user_id, order_id, product_id, rating, comment, status) 
           VALUES (?, ?, ?, ?, ?, 'pending')""",
        (user_id, order_id, product_id, rating, comment)
    )
    review_id = cursor.lastrowid
    
    conn.commit()
    conn.close()
    return review_id

def get_approved_reviews(product_id: int = None):
    """Получение одобренных отзывов (для всех товаров или конкретного)"""
    conn = get_db_connection()
    if product_id:
        reviews = conn.execute(
            """SELECT r.*, u.username, u.first_name 
               FROM reviews r 
               JOIN users u ON r.user_id = u.user_id 
               WHERE r.status = 'approved' AND r.product_id = ?
               ORDER BY r.created_at DESC""",
            (product_id,)
        ).fetchall()
    else:
        reviews = conn.execute(
            """SELECT r.*, u.username, u.first_name, p.name as product_name 
               FROM reviews r 
               JOIN users u ON r.user_id = u.user_id 
               JOIN products p ON r.product_id = p.id 
               WHERE r.status = 'approved'
               ORDER BY r.created_at DESC""",
        ).fetchall()
    conn.close()
    return reviews

def get_pending_reviews():
    """Получение отзывов, ожидающих модерации"""
    conn = get_db_connection()
    reviews = conn.execute(
        """SELECT r.*, u.username, u.first_name, p.name as product_name 
           FROM reviews r 
           JOIN users u ON r.user_id = u.user_id 
           JOIN products p ON r.product_id = p.id 
           WHERE r.status = 'pending'
           ORDER BY r.created_at ASC""",
    ).fetchall()
    conn.close()
    return reviews

def get_user_reviews(user_id: int):
    """Получение отзывов пользователя"""
    conn = get_db_connection()
    reviews = conn.execute(
        """SELECT r.*, p.name as product_name 
           FROM reviews r 
           JOIN products p ON r.product_id = p.id 
           WHERE r.user_id = ?
           ORDER BY r.created_at DESC""",
        (user_id,)
    ).fetchall()
    conn.close()
    return reviews

def moderate_review(review_id: int, status: str, moderator_id: int = None):
    """Модерация отзыва (approve/reject)"""
    conn = get_db_connection()
    conn.execute(
        """UPDATE reviews 
           SET status = ?, moderated_at = CURRENT_TIMESTAMP 
           WHERE id = ?""",
        (status, review_id)
    )
    conn.commit()
    conn.close()

def get_review_stats(product_id: int = None):
    """Получение статистики по отзывам"""
    conn = get_db_connection()
    if product_id:
        stats = conn.execute(
            """SELECT 
                COUNT(*) as total_reviews,
                AVG(rating) as avg_rating,
                SUM(CASE WHEN rating = 5 THEN 1 ELSE 0 END) as five_star,
                SUM(CASE WHEN rating = 4 THEN 1 ELSE 0 END) as four_star,
                SUM(CASE WHEN rating = 3 THEN 1 ELSE 0 END) as three_star,
                SUM(CASE WHEN rating = 2 THEN 1 ELSE 0 END) as two_star,
                SUM(CASE WHEN rating = 1 THEN 1 ELSE 0 END) as one_star
            FROM reviews 
            WHERE status = 'approved' AND product_id = ?""",
            (product_id,)
        ).fetchone()
    else:
        stats = conn.execute(
            """SELECT 
                COUNT(*) as total_reviews,
                AVG(rating) as avg_rating
            FROM reviews 
            WHERE status = 'approved'"""
        ).fetchone()
    conn.close()
    return stats

# Инициализация БД при импорте
init_db()
