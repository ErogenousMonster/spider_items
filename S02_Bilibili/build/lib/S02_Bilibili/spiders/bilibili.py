# -*- coding: utf-8 -*-
import re
import redis
import json


import scrapy
from ..items import *


class BilibiliSpider(scrapy.Spider):
    name = 'bilibili'
    allowed_domains = ['bilibili.com']
    start_urls = ['https://www.bilibili.com/']
    user_info_url = 'https://api.bilibili.com/x/space/acc/info?mid={}'
    fan_follow_num_url = 'https://api.bilibili.com/x/relation/stat?vmid={}'
    fans_param = 'followers'
    follow_param = 'followings'
    fan_follow_list_url = 'https://api.bilibili.com/x/relation/{}?vmid={}'

    def __init__(self, settings, *args, **kwargs):
        super(BilibiliSpider, self).__init__(*args, **kwargs)
        self.redis_host = settings.get('REDIS_HOST', '127.0.0.1')
        self.redis_port = settings.get('REDIS_PORT', 6379)
        self.redis_db = settings.get('REDIS_DB', '1')
        self.redis_key = settings.get('REDIS_KEY', 'user')
        self.con = redis.Redis(
            host=self.redis_host,
            port=self.redis_port,
            db=self.redis_db,
            decode_responses=True
        )

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = cls(crawler.settings, *args, **kwargs)
        spider._set_crawler(crawler)
        return spider

    def parse(self, response):
        """
        拿出首页所有的用户 mid
        :param response:
        :return:
        """
        mid_list = re.findall(r'"mid":(\d+),', response.text)
        for mid in mid_list:
            yield scrapy.Request(url=self.user_info_url.format(mid),
                                 meta={'mid': mid}, callback=self.parse_user)

    def parse_user(self, response):
        mid = response.meta.get('mid')
        # 如果不在 redis set 则继续爬取
        if not self.con.sismember(self.redis_key, mid):
            self.con.sadd(self.redis_key, mid)
            json_dict = json.loads(response.text)
            user_item = UserInfoItem()
            json_data = json_dict.get('data')
            # 有数据再存入
            if json_data:
                # 设置默认值，防止没有数据
                user_item['name'] = json_data.get('name', 'NULL')
                user_item['mid'] = json_data.get('mid', 'NULL')
                user_item['sex'] = json_data.get('sex', 'NULL')
                user_item['vip_type'] = json_data.get('vip').get('type')
                user_item['birthday'] = json_data.get('birthday', 'NULL')

            # follow data
            yield scrapy.Request(url=self.fan_follow_list_url.format(self.follow_param, mid),
                                 callback=self.parse_follow_fans)
            # fans data
            yield scrapy.Request(url=self.fan_follow_list_url.format(self.fans_param, mid),
                                 callback=self.parse_follow_fans)
            yield scrapy.Request(url=self.fan_follow_num_url.format(mid),
                                 meta={'mid': mid, 'item': user_item}, callback=self.parse_num)

    def parse_num(self, response):
        user_item = response.meta.get('item')
        json_dict = json.loads(response.text)
        json_data = json_dict.get('data')
        if json_data:
            follow_num = json_data.get('follow', '0')
            fans_num = json_data.get('fans', '0')
            user_item['follow'] = follow_num
            user_item['fans'] = fans_num

        yield user_item

    def parse_follow_fans(self, response):
        json_dict = json.loads(response.text)
        json_data = json_dict.get('data')
        if json_data:
            json_list = json_data.get('list')
            if json_list:
                for json_item in json_list:
                    mid = json_item.get('mid')
                    if mid:
                        yield scrapy.Request(url=self.user_info_url.format(mid),
                                             meta={'mid': mid}, callback=self.parse_user)

