from aiogram.fsm.state import State, StatesGroup

class OrderStates(StatesGroup):
    choosing_tariff = State()
    entering_description = State()
    waiting_for_payment = State()
    in_development = State()
    waiting_for_token = State()
    admin_login = State()
    admin_waiting_message = State()
    admin_in_panel = State()
    waiting_for_review_text = State()
    waiting_for_review_rating = State()
