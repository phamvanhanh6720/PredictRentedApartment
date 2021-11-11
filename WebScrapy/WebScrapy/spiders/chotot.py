import scrapy


class ChototSpider(scrapy.Spider):
    name = 'chotot'
    allowed_domains = ['nha.chotot.com']
    start_urls = ['http://nha.chotot.com/']

    def parse(self, response):
        pass
