import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime as dt
from io import TextIOWrapper

from blog_post import BlogPost

logger = logging.getLogger(__name__)


class Page:

    def __init__(self, url, filepath=None):
        self.url = url
        self.filepath = filepath
        self.blog_posts = []

    def get_blog_posts(self, data_from="web"):
        if data_from == "web":
            if self.url:
                html_data = requests.get(self.url).content
            else:
                raise ValueError("No url provided")
        elif data_from == "local":
            if self.filepath:
                html_data = open(self.filepath)
            else:
                raise ValueError("No filepath provided")
        else:
            raise ValueError("Invalid operation selected")
        self._get_blog_posts_inner(html_data)

    def _get_blog_posts_inner(self, html_data):
        blog_posts = []
        soup = BeautifulSoup(html_data, 'html.parser')
        for date_outer in soup.find_all("div", class_="date-outer"):
            date = self.get_date(date_outer)
            for post_outer in soup.find_all("div", class_="post-outer"):
                blog_post = BlogPost(self.url, self.filepath, post_outer, date).prepare(False)
                if not blog_post.is_unneeded_post:
                    blog_posts.append(blog_post)
                    logger.debug([(g.home_team, g.home_score, g.away_score, g.away_team) for g in
                                  blog_posts[-1].games])
        self.blog_posts = blog_posts

        if isinstance(html_data, TextIOWrapper):
            html_data.close()

    @staticmethod
    def get_date(soup):
        return dt.strptime(list(list(soup.find_all("h2", class_="date-header")[0].children)[0].children)[0],
                           '%A, %B %d, %Y')