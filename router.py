import webapp2

from index import IndexHandler
from auth import LoginHandler
from article import SubmitArticleHandler, ViewArticleHandler, AddCommentHandler
from vote import VoteHandler

# Here we can set up more advanced routing rules
APP = webapp2.WSGIApplication([
    (r'/', IndexHandler),
    (r'/login', LoginHandler),
    (r'/submit', SubmitArticleHandler),
    (r'/article/(\d+)', ViewArticleHandler),
    (r'/article/(\d+)/comment', AddCommentHandler),
    (r'/vote/(\d+)/(\w+)', VoteHandler),
], debug=True)

