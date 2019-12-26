# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class S02BilibiliItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class UserInfoItem(scrapy.Item):
    # define the fields for your item here like:
    name = scrapy.Field()  # 用户名
    mid = scrapy.Field()  # 用户id
    sex = scrapy.Field()  # 用户性别
    follow = scrapy.Field()  # 用户关注数
    fans = scrapy.Field()  # 用户粉丝数
    vip_type = scrapy.Field()  # vip 0：非会员 1：大会员 2：年度大会员
