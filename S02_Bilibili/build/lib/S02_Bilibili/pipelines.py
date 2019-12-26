# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import pymongo
from twisted.internet import reactor, defer


class S02BilibiliPipeline(object):
    def process_item(self, item, spider):
        return item


class MongoPipline(object):
    """
    异步插入MongoDB
    """
    def __init__(self, mongo_uri, mongo_db, mongo_col):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db
        self.mongo_col = mongo_col

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_HOST', '127.0.0.1'),
            mongo_db=crawler.settings.get('MONGO_DB'),
            mongo_col=crawler.settings.get('MONGO_COL'),
        )

    def open_spider(self, spider):
        """
        爬虫启动时，启动
        :param spider:
        :return:
        """
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.mongodb = self.client[self.mongo_db]

    def close_spider(self, spider):
        """
        爬虫关闭时执行
        :param spider:
        :return:
        """
        self.client.close()

    @defer.inlineCallbacks
    def process_item(self, item, spider):
        out = defer.Deferred()
        reactor.callInThread(self._insert, item, out, spider)
        yield out
        defer.returnValue(item)

    def _insert(self, item, out, spider):
        """
        插入函数
        :param item:
        :param out:
        :return:
        """
        self.mongodb[self.mongo_col].insert(dict(item))
        reactor.callFromThread(out.callback, item)
