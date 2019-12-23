# -*- coding: utf-8 -*-
import re
import os


import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from scrapy.selector import Selector


from ..items import *
from w3lib.html import remove_tags


class CnblogsSpider(CrawlSpider):
    name = 'cnblogs'
    allowed_domains = ['www.cnblogs.com']
    start_urls = ['https://www.cnblogs.com/']

    rules = (
        Rule(LinkExtractor(allow=(r'/\d+.html',), deny=(r'/category/.*?\.html',)),
             callback='parse_item', follow=True),
    )

    def __init__(self, *a, **kw):
        super(CrawlSpider, self).__init__(*a, **kw)
        self._compile_rules()

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(CrawlSpider, cls).from_crawler(crawler, *args, **kwargs)
        spider._follow_links = crawler.settings.getbool(
            'CRAWLSPIDER_FOLLOW_LINKS', True)
        return spider

    def parse_item(self, response):
        article_loader = TakeFirstItemLoader(item=ArticleItem(), response=response)

        # 从url中得出id
        url = response.url
        articel_id = re.match('.*/(\d+)\.html', url).group(1)

        # 存入item
        article_loader.add_value('articel_id', articel_id)
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
                                format(blog_id, articel_id, blog_user_guid))

        # 用户界面提取
        yield scrapy.Request(base_url, callback=self.parse_author, meta={'blog_user_guid': blog_user_guid})
        # 文章界面提取
        yield scrapy.Request(url=blog_url, meta={'loader': article_loader, 'articel_id': articel_id,
                                                 'base_url': base_url}, callback=self.parse_digg)

    def parse_digg(self, response):
        article_loader = response.meta.get('loader')
        base_url = response.meta.get('base_url')
        articel_id = response.meta.get('articel_id')

        article_loader.selector = Selector(response)
        author_url = response.css('#author_profile_detail a:nth-child(1)::attr(href)').get()
        author_url = response.urljoin(author_url)
        article_loader.add_css('author', '#author_profile_detail a:nth-child(1)::text')
        article_loader.add_value('author_url', author_url)
        article_loader.add_css('digg_num', '#digg_count::text')
        article_loader.add_css('bury_num', '#bury_count::text')

        # 采用软编码，其实上面urljoin已经处理过了，但是我就想写
        yield response.follow(url=author_url, callback=self.parse_author)
        view_url = os.path.join(base_url + '/ajax/GetViewCount.aspx?postID={}'.format(articel_id))
        yield scrapy.Request(url=view_url, meta={'loader': article_loader, 'articel_id': articel_id,
                                                 'base_url': base_url}, callback=self.parse_view)

    def parse_view(self, response):
        article_loader = response.meta.get('loader')
        base_url = response.meta.get('base_url')
        articel_id = response.meta.get('articel_id')

        article_loader.add_value('view_num', response.text)

        comment_url = os.path.join(base_url + '/ajax/GetCommentCount.aspx?postID={}'.format(articel_id))
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
        author_loader.add_css('articel_num', '#stats_article_count::text')
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
