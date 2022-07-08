from re import T
import redis

class redisDB():
    def __init__(self):
        self.r = redis.StrictRedis(host='localhost', port=6379, db=0, password='potato', decode_responses=True)
    
    # Reading redis
    def read(self, type:str, key:str):
        if type == "hash":
            return self.r.hgetall(key)
        if type == "json":
            return self.r.json().get(key) 
    
    # position for hash is the key
    # position for json is the key at root 
    # Examples
    # # redisDB.redisDB().write("json", "entries", "220628", "{"start":"", "end":"", "status":"2"}")
    # # redisDB.redisDB().write("hash", "config", "lastStatus", 2)
    def write(self, type:str, key:str, position:str, data):
        if type == "hash":
            a = self.r.hset(key, position, data)
            return a
        if type == "json":
            a = self.r.json().set(key, position, data, nx=False, xx=False) ## nx=False, xx=False allowing overwriting
            return a