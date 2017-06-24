from importlib import import_module
import os
import pickle
from time import time

from crawlmi.http import Headers
from crawlmi.http.response.factory import from_args
from crawlmi.utils.request import request_fingerprint


class DbmCacheStorage(object):

    def __init__(self, engine):
        project = engine.project
        settings = engine.settings

        self.engine = engine
        self.cache_dir = project.data_path(settings['HTTP_CACHE_DIR'],
                                           create_dir=True)
        self.expiration_secs = settings.get_int('HTTP_CACHE_EXPIRATION_SECS')
        self.db_module = import_module(settings['HTTP_CACHE_DBM_MODULE'])
        self.db = None

    def open(self):
        dbpath = os.path.join(self.cache_dir, '%s.db' % self.engine.spider.name)
        self.db = self.db_module.open(dbpath, 'c')

    def close(self):
        self.db.close()

    def retrieve_response(self, request):
        data = self._read_data(request)
        if data is None:
            return  # not cached
        url = data['url']
        status = data['status']
        headers = Headers(data['headers'])
        body = data['body']
        respcls = from_args(headers=headers, url=url)
        response = respcls(url=url, headers=headers, status=status, body=body)
        return response

    def store_response(self, request, response):
        key = self._request_key(request)
        data = {
            'status': response.status,
            'url': response.url,
            'headers': dict(response.headers),
            'body': response.body,
        }
        self.db['%s_data' % key] = pickle.dumps(data, protocol=2)
        self.db['%s_time' % key] = str(time())

    def _read_data(self, request):
        key = self._request_key(request)
        db = self.db
        tkey = '%s_time' % key
        if tkey not in db:
            return  # not found

        ts = db[tkey]
        if 0 < self.expiration_secs < time() - float(ts):
            return  # expired

        return pickle.loads(db['%s_data' % key])

    def _request_key(self, request):
        return request_fingerprint(request)
