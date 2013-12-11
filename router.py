import webapp2

from index import IndexHandler
from auth import LoginHandler
from article import AddArticleHandler, ViewArticleHandler, AddCommentHandler
from vote import AddVoteHandler

# Here we can set up more advanced routing rules
APP = webapp2.WSGIApplication([
    (r'/', IndexHandler),
    (r'/login', LoginHandler),
    (r'/submit', AddArticleHandler),
    (r'/article/(\d+)', ViewArticleHandler),
    (r'/article/(\d+)/comment', AddCommentHandler),
    (r'/vote/(\d+)/(\w+)', AddVoteHandler),
], debug=True)

