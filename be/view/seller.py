from flask import Blueprint, request, jsonify
from bookstore.be.view.auth_required import auth_required
from bookstore.be.model import seller
import json

bp_seller = Blueprint('seller', __name__, url_prefix='/seller')

@auth_required
def create_store():
    user_id: str = request.json.get("user_id")
    store_id: str = request.json.get("store_id")
    s = seller.Seller()
    code, message = s.create_store(user_id, store_id)
    return jsonify({"message": message}), code

@auth_required
def add_book():
    user_id: str = request.json.get("user_id")
    store_id: str = request.json.get("store_id")
    book_info: str = request.json.get("book_info")
    stock_level: str = request.json.get("stock_level", 0)

    s = seller.Seller()
    code, message = s.add_book(user_id, store_id, book_info, stock_level)
    return jsonify({"message": message}), code

@auth_required
def add_stock_level():
    user_id: str = request.json.get("user_id")
    store_id: str = request.json.get("store_id")
    book_id: str = request.json.get("book_id")
    add_stock_level_num: str = request.json.get("add_stock_level", 0)

    s = seller.Seller()
    code, message = s.add_stock_level(user_id, store_id, book_id, add_stock_level_num)
    return jsonify({"message": message}), code

@auth_required
def deliver_order():
    user_id: str = request.json.get("user_id")
    store_id: str = request.json.get("store_id")
    order_id: str = request.json.get("order_id")

    s = seller.Seller()
    code, message = s.deliver_order(user_id, store_id, order_id)
    return jsonify({"message": message}), code

bp_seller.add_url_rule('/create_store', methods=['POST'], view_func=create_store)
bp_seller.add_url_rule('/add_book', methods=['POST'], view_func=add_book)
bp_seller.add_url_rule('/add_stock_level', methods=['POST'], view_func=add_stock_level)
bp_seller.add_url_rule('/deliver_order', methods=['POST'], view_func=deliver_order)
