from datetime import datetime
from config import orders, reviews, order_counter, review_counter, Order, Tariff

def create_order(user_id: int, username: str, tariff: Tariff, description: str) -> int:
    global order_counter
    order_counter += 1
    order = Order(
        id=order_counter,
        user_id=user_id,
        username=username,
        tariff=tariff,
        description=description,
        status='pending',
        created_at=datetime.now(),
        paid=False
    )
    orders[order_counter] = order
    return order_counter

def get_order(order_id: int):
    return orders.get(order_id)

def mark_order_paid(order_id: int):
    if order_id in orders:
        orders[order_id].paid = True
        orders[order_id].status = 'development'

def get_user_orders(user_id: int) -> list:
    return [o for o in orders.values() if o.user_id == user_id]

def create_review(user_id: int, username: str, rating: int, text: str, order_id: int = None) -> int:
    global review_counter
    review_counter += 1
    
    review = {
        'id': review_counter,
        'user_id': user_id,
        'username': username,
        'rating': rating,
        'text': text,
        'date': datetime.now(),
        'approved': False,
        'order_id': order_id
    }
    reviews.append(review)
    return review_counter

def get_approved_reviews() -> list:
    return [r for r in reviews if r.get('approved', False)]

def approve_review(review_id: int) -> bool:
    for review in reviews:
        if review['id'] == review_id:
            review['approved'] = True
            return True
    return False

def reject_review(review_id: int):
    global reviews
    reviews = [r for r in reviews if r['id'] != review_id]

def get_stats():
    total_orders = len(orders)
    completed = len([o for o in orders.values() if o.status == 'completed'])
    paid = len([o for o in orders.values() if o.paid])
    total_stars = sum([o.tariff.value[1] for o in orders.values() if o.paid])
    
    return {
        'total_orders': total_orders,
        'completed': completed,
        'paid': paid,
        'total_stars': total_stars,
        'reviews_count': len(get_approved_reviews())
    }
