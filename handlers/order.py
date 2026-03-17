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
    
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=keyboard
    )
    await callback.answer()

@router.message(OrderStates.waiting_for_quantity)
async def process_quantity(message: Message, state: FSMContext):
    """Обработка количества товара"""
    try:
        quantity = int(message.text)
        if quantity < 1 or quantity > 10:
            await message.answer("❌ Пожалуйста, введите число от 1 до 10.")
            return
        
        data = await state.get_data()
        product_id = data.get('product_id')
        product = get_product(product_id)
        
        if not product:
            await message.answer("❌ Товар не найден.")
            await state.clear()
            return
        
        total_price = product['price'] * quantity
        
        await state.update_data(quantity=quantity, total_price=total_price)
        
        text = f"✅ *Подтверждение заказа*\n\n"
        text += f"*Товар:* {product['name']}\n"
        text += f"*Количество:* {quantity}\n"
        text += f"*Цена за ед.:* {product['price']} руб.\n"
        text += f"*Итого:* {total_price} руб.\n\n"
        text += "Подтверждаете заказ?"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_order"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_order")
            ]
        ])
        
        await message.answer(text, parse_mode="Markdown", reply_markup=keyboard)
        await state.set_state(OrderStates.waiting_for_confirmation)
        
    except ValueError:
        await message.answer("❌ Пожалуйста, введите число.")

@router.callback_query(F.data == "confirm_order")
async def confirm_order(callback: CallbackQuery, state: FSMContext):
    """Подтверждение заказа"""
    data = await state.get_data()
    user_id = callback.from_user.id
    product_id = data.get('product_id')
    quantity = data.get('quantity')
    
    order_id = create_order(user_id, product_id, quantity)
    
    if order_id:
        await callback.message.edit_text(
            f"✅ *Заказ оформлен!*\n\n"
            f"Номер заказа: #{order_id}\n"
            f"Статус: ожидает обработки\n\n"
            f"После получения заказа вы сможете оставить отзыв.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🛍 Продолжить покупки", callback_data="catalog")],
                [InlineKeyboardButton(text="📝 Оставить отзыв", callback_data="leave_review")],
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main")]
            ])
        )
    else:
        await callback.message.edit_text("❌ Ошибка при оформлении заказа.")
    
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "cancel_order")
async def cancel_order(callback: CallbackQuery, state: FSMContext):
    """Отмена заказа"""
    await state.clear()
    await callback.message.edit_text(
        "❌ Заказ отменен.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🛍 В каталог", callback_data="catalog")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main")]
        ])
    )
    await callback.answer()

@router.callback_query(F.data == "my_orders")
async def my_orders(callback: CallbackQuery):
    """Показать заказы пользователя"""
    user_id = callback.from_user.id
    orders = get_user_orders(user_id)
    
    if not orders:
        await callback.message.edit_text(
            "🛒 У вас пока нет заказов.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🛍 В каталог", callback_data="catalog")],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
            ])
        )
        await callback.answer()
        return
    
    text = "🛒 *Мои заказы:*\n\n"
    for order in orders[:5]:
        status_emoji = {
            'pending': '⏳',
            'processing': '🔄',
            'completed': '✅',
            'delivered': '📦',
            'cancelled': '❌'
        }.get(order['status'], '📝')
        
        text += f"{status_emoji} *Заказ #{order['id']}*\n"
        text += f"Товар: {order['product_name']}\n"
        text += f"Кол-во: {order['quantity']}\n"
        text += f"Сумма: {order['total_price']} руб.\n"
        text += f"Статус: {order['status']}\n"
        text += f"Дата: {order['order_date'][:10]}\n\n"
    
    keyboard = [
        [InlineKeyboardButton(text="📝 Оставить отзыв", callback_data="leave_review")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ]
    
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await callback.answer()
