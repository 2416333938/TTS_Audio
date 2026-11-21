def read_api_key():
    with open(".env", "r") as f:
        return f.readline().strip()