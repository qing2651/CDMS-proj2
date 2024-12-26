error_code = {
    400: "bad request: {}",
    401: "authorization fail: {}",
    403: "forbidden: {}",
    404: "resource not found: {}",
    511: "non exist user id: {}",
    512: "exist user id: {}",
    513: "non exist store id: {}",
    514: "exist store id: {}",
    515: "non exist book id: {}",
    516: "exist book id: {}",
    517: "stock level low, book id: {}",
    518: "invalid order id: {}",
    519: "not sufficient funds, order id: {}",
    530: "internal server error: {}"
}


def error_non_exist_user_id(user_id):
    return 511, error_code[511].format(user_id)


def error_exist_user_id(user_id):
    return 512, error_code[512].format(user_id)


def error_non_exist_store_id(store_id):
    return 513, error_code[513].format(store_id)


def error_exist_store_id(store_id):
    return 514, error_code[514].format(store_id)


def error_non_exist_book_id(book_id):
    return 515, error_code[515].format(book_id)


def error_exist_book_id(book_id):
    return 516, "book_id already exists: {}".format(book_id)


def error_stock_level_low(book_id):
    return 517, error_code[517].format(book_id)


def error_invalid_order_id(order_id):
    return 518, error_code[518].format(order_id)


def error_not_sufficient_funds(order_id):
    return 519, error_code[519].format(order_id)


def error_authorization_fail(reason=""):
    return 401, error_code[401].format(reason)


def error_bad_request(reason=""):
    return 400, error_code[400].format(reason)


def error_forbidden(reason=""):
    return 403, error_code[403].format(reason)


def error_not_found(reason=""):
    return 404, error_code[404].format(reason)


def error_internal(reason=""):
    return 530, error_code[530].format(reason)


def error_and_message(code, message):
    if code in error_code:
        return code, error_code[code].format(message)
    return code, message
