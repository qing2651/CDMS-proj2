from flask import Blueprint, request, jsonify
from bookstore.be.model import buyer
from bookstore.be.view.auth_required import auth_required

bp_buyer = Blueprint('buyer', __name__, url_prefix='/buyer')

@bp_buyer.route('/new_order', methods=['POST'])
@auth_required
def new_order():
    user_id = request.json.get('user_id')
    store_id = request.json.get('store_id')
    books = request.json.get('books')
    id_and_count = []
    for book in books:
        book_id = book.get('id')
        count = book.get('count')
        id_and_count.append((book_id, count))

    b = buyer.Buyer()
    code, message, order_id = b.new_order(user_id, store_id, id_and_count)
    return jsonify({'message': message, 'order_id': order_id}), code

@bp_buyer.route('/payment', methods=['POST'])
@auth_required
def payment():
    user_id = request.json.get('user_id')
    order_id = request.json.get('order_id')
    password = request.json.get('password')

    b = buyer.Buyer()
    code, message = b.payment(user_id, password, order_id)
    return jsonify({'message': message}), code

@bp_buyer.route('/add_funds', methods=['POST'])
@auth_required
def add_funds():
    user_id = request.json.get('user_id')
    password = request.json.get('password')
    add_value = request.json.get('add_value')

    b = buyer.Buyer()
    code, message = b.add_funds(user_id, password, add_value)
    return jsonify({'message': message}), code

@bp_buyer.route('/receive', methods=['POST'])
@auth_required
def receive():
    user_id = request.json.get('user_id')
    order_id = request.json.get('order_id')

    b = buyer.Buyer()
    code, message = b.receive(user_id, order_id)
    return jsonify({'message': message}), code
