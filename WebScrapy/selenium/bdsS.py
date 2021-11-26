from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from selenium import webdriver
from selenium.webdriver.common.keys import Keys



class BatDongSan():
    def __init__(self):
        self.driver = webdriver.Chrome('C:/Users/Admin/Downloads/chromedriver')

    def parse(self):
        self.driver.get("https://batdongsan.com.vn/cho-thue-can-ho-chung-cu-ha-noi/p1")
        search_bar = self.driver.find_elements_by_css_selector('a.js__product-link-for-product-id')
        news_url_list = []
        size_page = search_bar.__len__()
        for i in range(size_page):
            news_url_list.append(search_bar[i].get_attribute('href'))
        news_url_list

        search_bar.clear()
        search_bar.send_keys("getting started")
        search_bar.send_keys(Keys.RETURN)
        self.driver.close()
if __name__ == "__main__":
    BatDongSan()
    print("ngu")
