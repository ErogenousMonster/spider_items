# -*- coding: utf-8 -*-
import re
import os


import scrapy
# from scrapy.linkextractors import LinkExtractor
# from scrapy.spiders import CrawlSpider, Rule
from scrapy.selector import Selector


from ..items import *
from w3lib.html import remove_tags


class CnblogsSpider(scrapy.Spider):
    name = 'cnblogs'
    allowed_domains = ['www.cnblogs.com']
    start_urls = ['https://www.cnblogs.com/']

    def parse(self, response):
        # 从网站分类获取全部的文章
        cate_list = response.css('#cate_item a::attr(href)')

        # 排除最后一个评论分类
        for cate in cate_list[:-1]:
            yield response.follow(url=cate, callback=self.parse_cate)

    def parse_cate(self, response):
        # 获取每个分类下的文章
        title_list = response.css('.titlelnk ::attr(href)')
        # 当前页的文章数小于20，说明是最后一页了
        if len(title_list) < 20:
            for title in title_list:
                yield response.follow(title, callback=self.parse_item)
        else:
            for title in title_list:
                yield response.follow(title, callback=self.parse_item)

            next_url = response.css('.last+ a::attr(href)')[0]
            yield response.follow(next_url, callback=self.parse_cate)

    def parse_item(self, response):
        # 从url中得出id
        url = response.url
        article_group = re.match('.*/(\d+)\.html', url)
        if article_group:
            article_loader = TakeFirstItemLoader(item=ArticleItem(), response=response)
            article_id = article_group.group(1)
            # 存入item
            article_loader.add_value('article_id', article_id)
            article_loader.add_css('title', '#cb_post_title_url::text')
            article_loader.add_value('url', url)
            content = remove_tags(response.css('#cnblogs_post_body').get())
            article_loader.add_value('content', content)
            article_loader.add_css('post_date', '#post-date::text')

            # author，digg, bury信息在另一个url中
            # https://www.cnblogs.com/du-hong/ajax/BlogPostInfo.aspx?blogId=378847&postId=12066776&blogUserGuid=a0df694d-7d0d-4efc-b565-08d4ef52ecb5
            # 获取 blogId 与 blogUserGuid
            blog_id = re.search(r"cb_blogId = (\d+)", response.text).group(1)
            blog_user_guid = re.search(r"cb_blogUserGuid = '(.*?)'", response.text).group(1)
            base_url = '/'.join(url.split('/')[:4])
            blog_url = os.path.join(base_url + '/ajax/BlogPostInfo.aspx?blogId={}&postId={}&blogUserGuid={}'.
                                    format(blog_id, article_id, blog_user_guid))

            # 用户界面提取
            yield scrapy.Request(base_url, callback=self.parse_author, meta={'blog_user_guid': blog_user_guid})
            # 文章界面提取
            yield scrapy.Request(url=blog_url, meta={'loader': article_loader, 'article_id': article_id,
                                                     'base_url': base_url}, callback=self.parse_digg)

    def parse_digg(self, response):
        article_loader = response.meta.get('loader')
        base_url = response.meta.get('base_url')
        article_id = response.meta.get('article_id')

        article_loader.selector = Selector(response)
        author_url = response.css('#author_profile_detail a:nth-child(1)::attr(href)').get()
        author_url = response.urljoin(author_url)
        article_loader.add_css('author', '#author_profile_detail a:nth-child(1)::text')
        article_loader.add_value('author_url', author_url)
        article_loader.add_css('digg_num', '#digg_count::text')
        article_loader.add_css('bury_num', '#bury_count::text')

        # 采用软编码，其实上面urljoin已经处理过了，但是我就想写
        view_url = os.path.join(base_url + '/ajax/GetViewCount.aspx?postID={}'.format(article_id))
        yield scrapy.Request(url=view_url, meta={'loader': article_loader, 'article_id': article_id,
                                                 'base_url': base_url}, callback=self.parse_view)

    def parse_view(self, response):
        article_loader = response.meta.get('loader')
        base_url = response.meta.get('base_url')
        article_id = response.meta.get('article_id')

        article_loader.add_value('view_num', response.text)

        comment_url = os.path.join(base_url + '/ajax/GetCommentCount.aspx?postID={}'.format(article_id))
        yield scrapy.Request(url=comment_url, meta={'loader': article_loader}, callback=self.parse_comment)

    def parse_comment(self, response):
        article_loader = response.meta.get('loader')
        article_loader.add_value('comment_num', response.text)

        article_item = article_loader.load_item()
        yield article_item

    def parse_author(self, response):
        url = response.url
        author_loader = TakeFirstItemLoader(item=AuthorItem(), response=response)

        author_loader.add_value('author_url_object_id', url)
        author_loader.add_value('author_url', url)
        author_loader.add_css('essay_num', '#stats_post_count::text')
        author_loader.add_css('article_num', '#stats_article_count::text')
        author_loader.add_css('comment_num', '#stats-comment_count::text')

        news_url = os.path.join(url + '/ajax/news.aspx')
        yield scrapy.Request(url=news_url, meta={'loader': author_loader, 'url': url}, callback=self.parse_news)

    def parse_news(self, response):
        author_loader = response.meta.get('loader')
        url = response.meta.get('url')

        author_loader.selector = Selector(response)
        author_loader.add_css('author', '#profile_block a:nth-child(1)::text')
        author_loader.add_css('registration_time', '#profile_block a:nth-child(3)::attr("title")')
        author_loader.add_css('fans_num', '#profile_block a:nth-child(5)::text')
        author_loader.add_css('follower_num', '#profile_block a:nth-child(7)::text')

        side_column_url = os.path.join(url + '/ajax/sidecolumn.aspx')

        yield scrapy.Request(url=side_column_url, meta={'loader': author_loader}, callback=self.parse_side)

    def parse_side(self, response):
        author_loader = response.meta.get('loader')
        author_loader.selector = Selector(response)
        author_loader.add_css('integral', '.liScore::text')
        author_loader.add_css('Ranking', '.liRank::text')

        author_item = author_loader.load_item()
        yield author_item
