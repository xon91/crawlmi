import random

from crawlmi.exceptions import NotConfigured


class RandomUserAgent(object):
    '''Use a random user agent for the request.
    It never hurts to hide a little.
    '''

    def __init__(self, engine):
        self.user_agents = engine.settings.get_list('RANDOM_USER_AGENT_LIST')
        if not self.user_agents:
            raise NotConfigured()

    def process_request(self, request):
        ua = random.choice(self.user_agents)
        request.headers.setdefault('User-Agent', ua)
        return request
