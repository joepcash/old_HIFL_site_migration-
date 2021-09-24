import requests
from bs4 import BeautifulSoup
import logging

from blog_post import BlogPost

logger = logging.getLogger(__name__)


class Page:

    def __init__(self, url):
        self.url = url

    def get_blog_posts(self):
        blog_posts = []
        page = requests.get(self.url)
        soup = BeautifulSoup(page.content, 'html.parser')
        for date_outer in soup.find_all("div", class_="date-outer"):
            blog_posts.append(BlogPost(date_outer))
            break
