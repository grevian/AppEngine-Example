import logging
import os
import webapp2

from google.appengine.api import taskqueue
from google.appengine.api import users
from google.appengine.ext import deferred
from google.appengine.ext import ndb

from models.content import Article
from models.vote import Vote, RatingsUpdateJob
from models.vote import UPVOTE, DOWNVOTE
from models.auth import JedditUser

RATINGS_QUEUE = 'update-ratings'

class AddVoteHandler(webapp2.RequestHandler):
  def post(self, article_id, vote_type): 
    article_id = int(article_id)
    article = Article.get_by_id(article_id)
    if not article:
      raise LookupError("Article %r could not be found!" % article_id)

    user = users.get_current_user()
    if not user:
      raise LookupError("Only logged in users may vote!")
    
    user_key = JedditUser.key_from_user(user)
    
    if vote_type == 'down':
      vote = Vote.create(article_key=article.key, user_key=user_key, value=DOWNVOTE)
    else:
      vote = Vote.create(article_key=article.key, user_key=user_key, value=UPVOTE)
    vote.put()

    # Add a task to the Pull Queue to update this articles rating
    queue = taskqueue.Queue(RATINGS_QUEUE)
    task = taskqueue.Task(payload=str(article_id), method='PULL')
    queue.add(task)

    return self.redirect('/', body="Thanks for your vote!")

  def get(self, article_id, vote_type):
    return self.post(article_id, vote_type)

class JobOverlapException(Exception):
  pass

def update_all_ratings():
  logging.info("Starting update_all_ratings")
  job = RatingsUpdateJob.get_by_id(RatingsUpdateJob.MARKER_ID)

  # Pull pending updates off the pull queue
  # TODO This should probably be in the transaction, or we should have a quick transaction check to
  # place the marker when this function first starts and not lease tasks until it returns
  queue = taskqueue.Queue(RATINGS_QUEUE)
  tasks = queue.lease_tasks(lease_seconds=600, max_tasks=1000, deadline=10)
  logging.info("Leased %d tasks" % len(tasks))

  # Get the unique set of article keys in need of updates and add them to the job
  article_keys = set()
  for t in tasks:
    article_keys.add(ndb.Key('Article', int(t.payload)))
  job.articles_updating = article_keys
  logging.info("Applying updates to %d articles, from %d tasks" % (len(article_keys), len(tasks)))

  # Ensure that the job being created and tasks being queued happen at the same time
  @ndb.transactional
  def start_job():
    # Write the job marker out, and start deleting tasks off the pull queue that are
    # being handled by this update
    job_future = job.put_async()
    queue_future = queue.delete_tasks_async(tasks)

    # By queuing update tasks in the transaction, we ensure they are successfully queued
    # but also that they will only run if the job is written properly, and the pull
    # queue is properly emptied
    for ak in article_keys:
      logging.debug("Queuing update_article_rating for article %r" % ak)
      deferred.defer(update_article_rating, ak.id())

    # If we failed to write the job, or remove the tasks from the queue, these will raise
    # exceptions and abort the transaction
    job_future.get_result()
    queue_future.get_result()

  start_job()

def update_article_rating(article_id):
  article_id = int(article_id)
  article = Article.get_by_id(article_id)
  if not article:
    raise LookupError("Article not found: %r" % article_id)
  article_key = article.key

  # TODO Calculate Article rating update
  import random
  article.rating = random.randint(1,20)

  # This is probably a good place to talk about transaction collisions, since they'll
  # almost certainly happen with this transaction. It's also a good place to talk about
  # Idempotency, since if a transaction can't be committed, this entire task will retry,
  # which should succeed 
  @ndb.transactional(xg=True)
  def update_job():
    job = RatingsUpdateJob.get_by_id(RatingsUpdateJob.MARKER_ID)

    # Remove this article from the list of those being updated by the job,
    # If this transaction commits then the update is complete
    articles_updating = set(job.articles_updating)
    articles_updating.remove(article_key)
    job.articles_updating = articles_updating
    
    # If this is the last update being applied by the job, run the final step of the
    # update workflow
    if not articles_updating:
      deferred.defer(complete_ratings_update)

    # Write the update article rating, and the job out in the transaction
    ndb.put_multi([job, article])
    logging.debug("Article rating set to %f for article %r" % (article.rating, article_key))
    logging.debug("Job has %d updates remaining" % len(job.articles_updating))

  update_job()   

def complete_ratings_update():
  # TODO re-run content.build_article_list and stick the results into memcache
  logging.info("Completing article rating update job")
  ndb.Key('RatingsUpdateJob', RatingsUpdateJob.MARKER_ID).delete() 

VOTE_APP = webapp2.WSGIApplication([
    (r'/vote/(\d+)/(\w+)', Vote),
], debug=True)

