from os.path import join, dirname
import random

from crawlmi.utils.conf import read_list_data_file


class RandomUserAgent(object):
    '''Use a random user agent for the request.
    It never hurts to hide a little.
    '''

    def __init__(self, engine):
        self.user_agents = engine.settings.get_list('RANDOM_USER_AGENT_LIST')
        if not self.user_agents:
            self.user_agents = read_list_data_file(join(dirname(__file__), 'user_agents.txt'))

    def process_request(self, request):
        user_agents = request.meta.get('RANDOM_USER_AGENT_LIST', self.user_agents)
        ua = random.choice(user_agents)
        request.headers.setdefault('User-Agent', ua)
        return request
