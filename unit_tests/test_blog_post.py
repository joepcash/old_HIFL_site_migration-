from unittest import TestCase
from bs4 import BeautifulSoup

from src.blog_post import BlogPost


class TestBlogPost(TestCase):

    def test_title_doesnt_contain_spaces_at_start(self):
        html_text = BeautifulSoup("""
<div class="post-outer">
<div class="post hentry uncustomized-post-template" itemprop="blogPost" itemscope="itemscope" itemtype="http://schema.org/BlogPosting">
<meta content="1961571526460637009" itemprop="blogId"/>
<meta content="6012340790707580167" itemprop="postId"/>
<a name="6012340790707580167"></a>
<h3 class="post-title entry-title" itemprop="name">
<a href="http://hanoiinternationalfootballleague.blogspot.com/2012/10/welcome-to-hifl-201213.html">Welcome to HIFL 2012/13</a>
</h3>
<div class="post-header">
<div class="post-header-line-1"></div>
</div>
<div class="post-body entry-content" id="post-body-6012340790707580167" itemprop="description articleBody">
Welcome to the 2012/13 season of the Hanoi International Football League!<br/>
- Dave
</div>
</div>
</div></div>""", "html.parser")
        blog_post = BlogPost("", "", html_text, "")
        blog_post.get_title()
        self.assertEqual("Welcome to HIFL 2012/13", blog_post.title)

    def test_get_hyperlinks_when_starting_square_bracket_and_lots_of_text(self):
        html_text = """[

**Week Thirteen**

  

Position

|

Team

|

P

|

W

|

D

|

L

|

F

|

A

|

GD

|


at  [7:40
AM](http://hanoiinternationalfootballleague.blogspot.com/2016/03/week-
thirteen-position-team-p-w-d-l-f.html "permanent link") [ No comments:
](http://hanoiinternationalfootballleague.blogspot.com/2016/03/week-thirteen-
position-team-p-w-d-l-f.html#comment-form) [
![](https://resources.blogblog.com/img/icon18_email.gif)
](https://www.blogger.com/email-
post.g?blogID=1961571526460637009&postID=7840077952037923546 "Email Post") [
![](https://resources.blogblog.com/img/icon18_edit_allbkg.gif)
](https://www.blogger.com/post-
edit.g?blogID=1961571526460637009&postID=7840077952037923546&from=pencil "Edit
Post")

"""
        expected = [('7:40\nAM',
                     'http://hanoiinternationalfootballleague.blogspot.com/2016/03/week-\nthirteen-position-team-p-w-d-l-f.html "permanent link"'),
                    (' No comments:\n',
                     'http://hanoiinternationalfootballleague.blogspot.com/2016/03/week-thirteen-\nposition-team-p-w-d-l-f.html#comment-form'),
                    ('', 'https://resources.blogblog.com/img/icon18_email.gif'),
                    ('', 'https://resources.blogblog.com/img/icon18_edit_allbkg.gif')]
        blog_post = BlogPost("", "", "", "")
        hyperlinks = blog_post.find_hyperlinks_in_text(html_text)
        self.assertEqual(hyperlinks, expected)

    def test_get_games_with_no_space_in_scores(self):
        text = "Drink 4-1 Roots"
        blog_post = BlogPost("", "", "", "")
        result = blog_post.find_games_in_text(text)
        expected = [("Drink 4-1 Roots", 'Drink', '4', '1', "Roots", "")]
        self.assertEqual(result, expected)

    def test_get_games_with_scorers_in_brackets(self):
        text = "Drink 4-1 Roots (Ben 40' Son 45' Thang 55' Thomas 75'; Baptiste 5')"
        blog_post = BlogPost("", "", "", "")
        result = blog_post.find_games_in_text(text)
        expected = [("Drink 4-1 Roots (Ben 40' Son 45' Thang 55' Thomas 75'; Baptiste 5')", 'Drink', '4', '1', "Roots",
                     "Ben 40' Son 45' Thang 55' Thomas 75'; Baptiste 5'")]
        self.assertEqual(result, expected)
