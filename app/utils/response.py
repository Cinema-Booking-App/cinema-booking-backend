def success_response(data):
    return {"status": "success", "data": data}

def error_response(message, code=None):
    resp = {"status": "error", "message": message}
    if code:
        resp["code"] = code
    return resp