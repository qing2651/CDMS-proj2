from flask import Blueprint
from flask import request
from flask import jsonify
from bookstore.be.model import user

bp_auth = Blueprint("auth", __name__, url_prefix="/auth")
user_manager = user.UserManager()

@bp_auth.route("/login", methods=["POST"])
def login():
    user_id = request.json.get("user_id", "")
    password = request.json.get("password", "")
    terminal = request.json.get("terminal", "")
    code, message, token = user_manager.login(user_id, password)
    if code == 0:
        return jsonify({"message": message, "token": token}), 200
    elif code == 1:
        return jsonify({"message": message}), 401  # 用户不存在
    else:
        return jsonify({"message": message}), 401  # 密码错误

@bp_auth.route("/register", methods=["POST"])
def register():
    user_id = request.json.get("user_id", "")
    password = request.json.get("password", "")
    code, message, token = user_manager.register(user_id, password)
    if code == 0:
        return jsonify({"message": message, "token": token}), 200
    elif code == 1:
        return jsonify({"message": message}), 409  # 用户已存在，使用409 Conflict
    else:
        return jsonify({"message": message}), 500  # 其他错误，使用500 Internal Server Error

@bp_auth.route("/password", methods=["POST"])
def change_password():
    user_id = request.json.get("user_id", "")
    old_password = request.json.get("oldPassword", "")
    new_password = request.json.get("newPassword", "")
    code, message = user_manager.change_password(user_id, old_password, new_password)
    if code == 0:
        return jsonify({"message": message}), 200
    elif code == 1:
        return jsonify({"message": message}), 401  # 用户不存在
    else:
        return jsonify({"message": message}), 401  # 密码错误

@bp_auth.route("/logout", methods=["POST"])
def logout():
    token = request.headers.get("token", "")
    code, message = user_manager.logout(token)
    if code == 0:
        return jsonify({"message": message}), 200
    else:
        return jsonify({"message": message}), 401  # token无效

@bp_auth.route("/unregister", methods=["POST"])
def unregister():
    user_id = request.json.get("user_id", "")
    password = request.json.get("password", "")
    code, message = user_manager.unregister(user_id, password)
    if code == 0:
        return jsonify({"message": message}), 200
    elif code == 1:
        return jsonify({"message": message}), 401  # 用户不存在
    else:
        return jsonify({"message": message}), 401  # 密码错误
