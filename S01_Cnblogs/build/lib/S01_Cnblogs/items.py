# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html
# from datetime import datetime
import re


import scrapy
from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst, MapCompose


import hashlib


def get_md5(url):
    if isinstance(url, str):
        url = url.encode('utf-8')
    m = hashlib.md5()
    m.update(url)

    return m.hexdigest()


def extract_num(content_num):
    num_group = re.search(r'(\d+)', content_num)
    if num_group:
        num = num_group.group(1)
        if num is not None:
            return num
        else:
            return 0
    else:
        return 0


# def convert_date(value):
#     # dateArray = datetime.fromtimestamp(value)
#     # otherStyleTime = dateArray.strptime("%Y-%m-%d %H:%M:%S")
#     # return otherStyleTime
#     try:
#         dateArray = time.strptime(value, '%Y-%m-%d %H:%M')
#     except:
#         dateArray = time.strptime(value, '%Y-%m-%d')
#
#     timeStamp = int(time.mktime(dateArray))
#     time_array = time.localtime(timeStamp)
#     return time.strftime("%Y-%m-%d %H:%M:%S", time_array)
    # print(timeStamp)


def extract_author(content_author):
    author_group = re.search(r'([^ |\n].*[^ |\n])', content_author)
    if author_group:
        return author_group.group(1)
    return ''


class TakeFirstItemLoader(ItemLoader):
    default_output_processor = TakeFirst()


class ArticleItem(scrapy.Item):
    # define the fields for your item here like:
    article_id = scrapy.Field()  # 文章链接的id，这里是用链接最后的数字作为id
    # 其实存在不是数字的情况，但是postid需要数字，所以排除不是数字的情况
    title = scrapy.Field()  # 文章标题
    url = scrapy.Field()  # 文章链接
    content = scrapy.Field()  # 正文
    author = scrapy.Field()  # 作者
    author_url = scrapy.Field()  # 作者
    digg_num = scrapy.Field()  # 推荐数
    bury_num = scrapy.Field()  # 反对数
    view_num = scrapy.Field()  # 阅读数
    comment_num = scrapy.Field()  # 评论数
    post_date = scrapy.Field(
        # input_processor=MapCompose(convert_date)
    )  # 发布时间

    def get_insert_sql(self):
        sql = """
        INSERT INTO article (article_id, title, url, content, author, author_url,
         digg_num, bury_num, view_num, comment_num, post_date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
         on DUPLICATE KEY UPDATE title=VALUES(title), content=VALUES(content), digg_num=VALUES(digg_num), 
         bury_num=VALUES(bury_num), view_num=VALUES(view_num), comment_num=VALUES(comment_num) 
        """

        params = []
        params.append(self.get('article_id', ''))
        params.append(self.get('title', ''))
        params.append(self.get('url', ''))
        params.append(self.get('content', ''))
        params.append(self.get('author', ''))
        params.append(self.get('author_url', ''))
        params.append(self.get('digg_num', 0))
        params.append(self.get('bury_num', 0))
        params.append(self.get('view_num', 0))
        params.append(self.get('comment_num', 0))
        params.append(self.get('post_date', '1970-01-01'))
        return sql, tuple(params)


class AuthorItem(scrapy.Item):
    # define the fields for your item here like:
    author_url_object_id = scrapy.Field(
        input_processor=MapCompose(get_md5)
    )  # 将用户主页作为id
    author = scrapy.Field(
        input_processor=MapCompose(extract_author)
    )  # 用户名
    author_url = scrapy.Field()  # 用户主页url
    essay_num = scrapy.Field(
        input_processor=MapCompose(extract_num)
    )  # 随笔数
    article_num = scrapy.Field(
        input_processor=MapCompose(extract_num)
    )  # 文章数
    comment_num = scrapy.Field(
        input_processor=MapCompose(extract_num)
    )  # 评论数
    registration_time = scrapy.Field(
        input_processor=MapCompose(lambda x: x[5:])
    )  # 入园时间
    fans_num = scrapy.Field(
        input_processor=MapCompose(extract_num)
    )  # 粉丝数目
    follower_num = scrapy.Field(
        input_processor=MapCompose(extract_num)
    )  # 关注人数
    integral = scrapy.Field(
        input_processor=MapCompose(extract_num)
    )  # 积分
    Ranking = scrapy.Field(
        input_processor=MapCompose(extract_num)
    )  # 排名

    def get_insert_sql(self):
        sql = """
        INSERT INTO author (author_url_object_id, author, author_url, essay_num, article_num, comment_num,
         registration_time, fans_num, follower_num, integral, Ranking) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
         on DUPLICATE KEY UPDATE essay_num=VALUES(essay_num), article_num=VALUES(article_num), 
         comment_num=VALUES(comment_num), fans_num=VALUES(fans_num), follower_num=VALUES(follower_num), 
         integral=VALUES(integral), Ranking=VALUES(Ranking)
        """

        params = []
        params.append(self.get('author_url_object_id', ''))
        params.append(self.get('author', ''))
        params.append(self.get('author_url', ''))
        params.append(self.get('essay_num', 0))
        params.append(self.get('article_num', 0))
        params.append(self.get('comment_num', 0))
        params.append(self.get('registration_time', '1970-01-01'))
        params.append(self.get('fans_num', 0))
        params.append(self.get('follower_num', 0))
        params.append(self.get('integral', 0))
        params.append(self.get('Ranking', 0))
        return sql, tuple(params)
