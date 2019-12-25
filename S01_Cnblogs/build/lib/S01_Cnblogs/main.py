import sys, os
from scrapy.cmdline import execute

# print(os.path.dirname(__file__))
# print(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(__file__))
execute(['scrapy', 'crawl', 'cnblogs'])
