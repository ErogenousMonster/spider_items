# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import pymysql
from twisted.enterprise import adbapi


class S01CnblogsPipeline(object):
    def process_item(self, item, spider):
        return item


# 同步插入数据库，可能出现重复的情况，不可取
# class MysqlPipeline(object):
#     def __init__(self, mysql_params):
#         self.db = mysql_params['db']
#         self.host = mysql_params['host']
#         self.port = mysql_params['port']
#         self.user = mysql_params['user']
#         self.password = mysql_params['password']
#
#     @classmethod
#     def from_crawler(cls, crawler):
#         mysql_params = {
#             'db': crawler.settings['MYSQLDATABASE'],
#             'host': crawler.settings['MYSQLHOST'],
#             'port': crawler.settings['MYSQLPORT'],
#             'user': crawler.settings['MYSQLUSER'],
#             'password': crawler.settings['MYSQLPWD'],
#         }
#         return cls(mysql_params)
#
#     def open_spider(self, spider):
#         self.db = pymysql.connect(database=self.db, host=self.host, port=self.port,
#                                   user=self.user, password=self.password)
#         self.cursor = self.db.cursor()
#
#     def process_item(self, item, spider):
#         insert_sql, params = item.get_insert_sql()
#         self.cursor.execute(insert_sql, params)
#         self.db.commit()
#         return item
#
#     # def close_spider(self, spider):
#     #     self.db.commit()


# 使用twisted异步存入数据库
class MysqlPipeline(object):
    def __init__(self, dbpool):
        self.dbpool = dbpool

    @classmethod
    def from_crawler(cls, crawler):
        mysql_params = {
            'db': crawler.settings['MYSQLDATABASE'],
            'host': crawler.settings['MYSQLHOST'],
            'port': crawler.settings['MYSQLPORT'],
            'user': crawler.settings['MYSQLUSER'],
            'password': crawler.settings['MYSQLPWD'],
        }
        dbpool = adbapi.ConnectionPool('pymysql', **mysql_params)
        return cls(dbpool)

    # def open_spider(self, spider):
    #     self.db = pymysql.connect(database=self.db, host=self.host, port=self.port,
    #                               user=self.user, password=self.password)
    #     self.cursor = self.db.cursor()

    def process_item(self, item, spider):
        query = self.dbpool.runInteraction(self.do_insert, item)
        query.addErrback(self.handle_error, item)
        return item

    def do_insert(self, cursor, item):
        insert_sql, params = item.get_insert_sql()
        cursor.execute(insert_sql, params)

    def handle_error(self, failure, item, spider):
        print(failure, '失败', item)

    # def close_spider(self, spider):
    #     self.db.commit()
