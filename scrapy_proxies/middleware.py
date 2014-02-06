# -*- coding: utf-8 -*-
import os
import json
import time
import random
import telnetlib

from scrapy import log
from scrapy import signals
from scrapy.contrib.downloadermiddleware import retry

from .agents import AGENTS


BASE_PATH = os.path.dirname(os.path.abspath(__file__))


class BaseHttpProxyMiddleware(object):

    def __init__(self, http_proxy):
        self._http_proxy = http_proxy

    def spider_opened(self, spider):
        """ signal receiver
        """
        self._http_proxy = getattr(spider, 'http_proxy', self._http_proxy)

    def process_request(self, request, spider):
        """ pre request
        """
        if self.use_proxy(request):
            try:
                request.meta['proxy'] = self._http_proxy
            except Exception, e:
                log.msg("Exception %s" % e, _level=log.CRITICAL)

    def use_proxy(self, request):
        """
        using direct download for depth <= 2
        using proxy with probability 0.3
        """
        # if "depth" in request.meta and int(request.meta['depth']) <= 2:
            # return False
        # i = random.randint(1, 10)
        # return i <= 2
        return True


class FAHttpProxyMiddleware(BaseHttpProxyMiddleware):
    """ Factory Automation http proxy provider.
    """
    @classmethod
    def from_crawler(cls, crawler):
        """ signal multiple spiders.
        """
        klass = cls(random.choice(json.loads(os.path.join(BASE_PATH, 'proxies.json'))))
        crawler.signals.connect(klass.spider_opened, signal=signals.spider_opened)
        return klass


class HttpProxyMiddleware(BaseHttpProxyMiddleware):
    """ fixed http proxy provider.
    """
    @classmethod
    def from_crawler(cls, crawler):
        """ signal multiple spiders.
        """
        http_proxy = crawler.settings.get('HTTP_PROXY', 'http://127.0.0.1:8123')
        klass = cls(http_proxy)
        crawler.signals.connect(klass.spider_opened, signal=signals.spider_opened)
        return klass


class RetryChangeProxyMiddleware(retry.RetryMiddleware):
    """ Fetching socks handshake provider
    """
    def _retry(self, request, reason, spider):
        log.msg('Operating change proxy to tor.')

        tn = telnetlib.Telnet('127.0.0.1', 9051)

        tn.read_until("Escape character is '^]'.", 2)
        tn.write('AUTHENTICATE "267765"\r\n')

        tn.read_until("250 OK", 2)
        tn.write("signal NEWNYM\r\n")

        tn.read_until("250 OK", 2)
        tn.write("quit\r\n")

        tn.close()

        time.sleep(5)
        log.msg('Proxy changed')
        return retry.RetryMiddleware._retry(self, request, reason, spider)


class UserAgentMiddleware(object):
    """ change request header nealy every time
    """
    def process_request(self, request, spider):
        agent = random.choice(AGENTS)
        request.headers['User-Agent'] = agent
