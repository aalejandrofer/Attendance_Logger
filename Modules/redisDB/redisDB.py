import redis

class redisDB():
    def __init__(self):
        self.r = redis.StrictRedis(host='localhost', port=6379, db=0, password='potato', decode_responses=True)
    
    def read(self, type:str, key:str):
        if type == "hash":
            return self.r.hgetall(key)
        if type == "json":
            return self.r.json().get(key) 