# token_store.py
chat_map = {}

def generate_token(chat_id):
    import uuid
    return str(uuid.uuid4())

def store_token_for_chat(token, chat_id):
    chat_map[token] = chat_id

def get_chat_id(token):
    return chat_map.get(token)