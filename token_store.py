# Simple in-memory maps
chat_map = {}
name_map = {}

def generate_token(chat_id):
    import uuid
    return str(uuid.uuid4())

def store_token_for_chat(token, chat_id):
    chat_map[token] = chat_id

def get_chat_id(token):
    return chat_map.get(token)

def store_name(token, name):
    name_map[token] = name

def get_name(token):
    return name_map.get(token)