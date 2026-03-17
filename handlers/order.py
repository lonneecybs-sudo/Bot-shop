from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import get_products, get_product, create_order, get_user_orders, get_categories

router = Router()

class OrderStates(StatesGroup):
    waiting_for_category = State()
    waiting_for_product = State()
    waiting_for_quantity = State()
    waiting_for_confirmation = State()

@router.callback_query(F.data == "catalog")
async def catalog(callback: CallbackQuery, state: FSMContext):
    """Показать каталог товаров"""
    categories = get_categories()
    
    keyboard = []
    for category in categories:
        keyboard.append([InlineKeyboardButton(text=f"📁 {category}", callback_data=f"cat_{category}")])
    keyboard.append([InlineKeyboardButton(text="🛒 Мои заказы", callback_data="my_orders")])
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")])
    
    await callback.message.edit_text(
        "🛍 *Каталог товаров*\n\nВыберите категорию:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("cat_"))
async def show_category(callback: CallbackQuery, state: FSMContext):
    """Показать товары категории"""
    category = callback.data[4:]
    products = get_products(category)
    
    if not products:
        await callback.message.edit_text(
            f"❌ В категории '{category}' пока нет товаров.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="catalog")]
            ])
        )
        await callback.answer()
        return
    
    text = f"📁 *Категория: {category}*\n\n"
    keyboard = []
    
    for product in products:
        text += f"*{product['name']}*\n"
        text += f"💰 Цена: {product['price']} руб.\n"
        text += f"📝 {product['description'][:50]}...\n\n"
        keyboard.append([InlineKeyboardButton(
            text=f"🛒 {product['name']} - {product['price']} руб.",
            callback_data=f"product_{product['id']}"
        )])
    
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="catalog")])
    
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("product_"))
async def show_product(callback: CallbackQuery, state: FSMContext):
    """Показать детали товара"""
    product_id = int(callback.data.split("_")[1])
    product = get_product(product_id)
    
    if not product:
        await callback.message.edit_text("❌ Товар не найден.")
        await callback.answer()
        return
    
    await state.update_data(product_id=product_id)
    
    text = f"*{product['name']}*\n\n"
    text += f"💰 *Цена:* {product['price']} руб.\n"
    text += f"📝 *Описание:* {product['description']}\n"
    text += f"📦 *В наличии:* {'Да' if product['in_stock'] else 'Нет'}\n\n"
    
    if product['in_stock']:
        text += "Введите количество товара для заказа (от 1 до 10):"
        await state.set_state(OrderStates.waiting_for_quantity)
    else:
        text += "❌ Товара нет в наличии."
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data=f"cat_{product['category']}")]
    ])
    
