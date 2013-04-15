# -*- coding: utf-8 -*-
from watson.http.sessions import StorageMixin
try:
    import memcache
except ImportError:
    pass


class MemcacheStorage(StorageMixin):
    """A memcache based storage adapter for session data.
    """
    client = None

    def __init__(self, id=None, timeout=None, autosave=True, config=None):
        super(MemcacheStorage, self).__init__(id, timeout, autosave)
        settings = {'servers': ['127.0.0.1:11211']}
        if not config:
            config = {}
        settings.update(config)
        self.config = settings

    def open(self):
        if not self.client:
            try:
                self.client = memcache.Client(self.config['servers'])
            except:
                raise ImportError('You must have python3-memcached installed.')

    def close(self):
        self.open()
        self.client.disconnect_all()
        return True

    def load(self):
        self._data = self._load() or {}

    def _load(self):
        self.open()
        return self.client.get(self.id)

    def _exists(self):
        return True if self.get(self.id) else False

    def _save(self, expires):
        self.open()
        self.client.set(self.id, self.data, self.timeout)

    def _destroy(self):
        self.open()
        self.client.delete(self.id)