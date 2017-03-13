
import time

class Timeout(object):
    '''
        Simple timeout helper in milliseconds.
    '''

    def __init__(self, timeout_ms):
        '''
            Start the expired counter instantly
        '''

        self.timeout_ms = timeout_ms
        self.start_time = time.time()

    def expired(self):
        '''
            Check if the timeout has expired
        '''
        return time.time() - self.start_time > self.timeout_ms / 1000.0
