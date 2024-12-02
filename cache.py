class Cache:
    _instance = None
    _cache = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def set(self, key, value):
        self._cache[key] = value

    def get(self, key):
        return self._cache.get(key)

    def delete(self, key):
        if key in self._cache:
            del self._cache[key]

    def clear(self):
        self._cache.clear()

# 创建全局单例实例
cache = Cache()