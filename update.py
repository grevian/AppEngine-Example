from datetime import datetime
import logging

from google.appengine.ext import deferred, ndb

from models import Upvote, Downvote, Article

def update_ratings(article_id=None):
  
  # Fan out and update every article
  if not article_id:
    logging.info("Fanning out to update articles")
    # Get all articles except those who have a rating so low no one would see them
    # Do a keys_only query because it's faster and because the keys are all we need here
    query = Article.query(default_options=ndb.QueryOptions(keys_only=True)).filter(Article.rating >= -10)
    for article_key in query:
      deferred.defer(update_ratings, article_id=article_key.id())
    return

  # Update only the given article
  article = Article.get_by_id(article_id)

  # Get a sum of both upvotes and downvotes at the same time
  upvote_count_future = Upvote.query().filter(Upvote.article==article.key).count_async()
  downvote_count_future = Downvote.query().filter(Downvote.article==article.key).count_async()

  # Calculate the ratios of upvotes to downvotes
  upvotes = max(upvote_count_future.get_result(), 1)
  downvotes = max(downvote_count_future.get_result(), 1)
  rating = float(upvotes) / float(downvotes)

  # Articles decay over time, by 0.5 per hour so figure out the decay and subtract it from the article rating
  decay = (article.submitted - datetime.now()).seconds/60/60
  rating = rating - (decay * 0.5)

  # Update the article and write it out
  logging.info("Updating Article %d to rating %f" % (article_id, rating))
  logging.info("Decay was %f, there were %d upvotes and %d downvotes" % (decay, upvotes, downvotes))
  article.rating = rating
  article.put()


