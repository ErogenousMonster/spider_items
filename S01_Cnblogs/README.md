#### 2019.12.23
1. 建立了cnblogs spider，爬取博客园内所有的文章信息及作者信息
2. 使用的是 crawlspider 模板，twisted 异步入库，articel、author两个数据表

#### 2019 12.25
1. 加入 AutoThrottle，对网站更友好（做文明爬虫~）
2. 更改代码逻辑（之前有错误），改用通用模板
3. scrapyd部署爬虫到服务器

##### 遇到的问题：
1. 分布式爬虫的部署，使用scrapy-redis时，由于yield的Request中meta传入了loader，因此报错`TypeError: can't pickle Selector objects`
   尚未解决