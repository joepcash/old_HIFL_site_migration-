import requests
from bs4 import BeautifulSoup
import logging
import urllib.request, urllib.error, urllib.parse
from pathlib import Path

logger = logging.getLogger(__name__)


class Blog:

    def __init__(self, url):
        self.url = url

    def get_all_page_urls(self):
        page_urls = []
        page = requests.get(self.url)
        page_urls.append(self.url)
        while True:
            soup = BeautifulSoup(page.content, 'html.parser')
            try:
                older_posts_link = soup.find_all("a", class_="blog-pager-older-link")[0].get("href")
                page_urls.append(older_posts_link)
                logger.debug(older_posts_link)
                page = requests.get(older_posts_link)
            except IndexError:
                break

        return page_urls

    def save_all_pages(self):
        Path("data/webpages").mkdir(parents=True, exist_ok=True)

        urls = self.get_all_page_urls()
        for i in range(len(urls)):
            logger.debug(f"Downloading {urls[i]}")
            response = urllib.request.urlopen(urls[i])
            webContent = response.read()

            f = open(f"data/webpages/page{i}.html", 'wb')
            f.write(webContent)
            f.close()