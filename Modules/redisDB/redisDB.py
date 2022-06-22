import redis as redisDB

class redis():
    def __init__(self):
        self.r = redisDB.StrictRedis(host='localhost', port=6379, db=0, password='potato')
    
    def read(self, type:str, key:str):
        if type == "hash":
            return self.r.hgetall(key)
        if type == "string":
            return self.r.get(key)
        if type == "stream":
            return self.r.xrange(key, 0, '+', 100)
