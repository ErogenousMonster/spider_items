#### 2019.12.23
1. 建立了cnblogs spider，爬取博客园内所有的文章信息及作者信息
2. 使用的是 crawlspider 模板，twisted 异步入库mysql，articel、author两个数据表

#### 2019 12.25
1. 加入 AutoThrottle，对网站更友好（做文明爬虫~）
2. 更改代码逻辑（之前有错误），改用通用模板
3. scrapyd部署爬虫到服务器

##### 遇到的问题：
1. 分布式爬虫的部署，使用scrapy-redis时，由于yield的Request中meta传入了loader，因此报错`TypeError: can't pickle Selector objects`
   尚未解决
   
#### 性能：
##### 2019.12.27
属性：单机爬虫

爬取时间：19:49:28

爬取文章总数：30426

爬取作者总数：9550

服务器属性：RAM: 1G, SWAP: 425.44MB, DISK: 20G, Operating system: Ubuntu 18.04 x86_64  
