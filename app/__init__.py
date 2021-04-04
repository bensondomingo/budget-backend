from redis import Redis

# banned_token_registry = Redis(host='redis', port='6379', db=3)
banned_token_registry = Redis(host='redis', port=6379, db=3)
