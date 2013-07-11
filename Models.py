from google.appengine.ext import db
import os
import jinja2
import webapp2
#from webapp2_extras import i18n
#from webapp2_extras.i18n import gettext as _
import unittest
from google.appengine.ext import testbed
import logging
import hashlib

template_dir = os.path.join(os.path.dirname(__file__), "../views")
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)
#jinja_env.install_gettext_translations(i18n)
jinja_unesc_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = False)


def render_str(template, **params):
	t = jinja_env.get_template(template)
	return t.render(params)

class User(db.Model):
	username = db.StringProperty(required=True)
	display_name = db.StringProperty()
	password = db.StringProperty(required=True)
	email_address = db.StringProperty(required=True)
	profile_img = db.BlobProperty()
	introduction = db.TextProperty(default=None)
	experience = db.IntegerProperty(default=0)
	birth_day = db.DateProperty()
	phone_number = db.PhoneNumberProperty(default=None)
	is_tasker = db.BooleanProperty(default=True)
	is_tasker_activated = db.BooleanProperty(default=True)
	paypal_email = db.StringProperty()
	facebook_id = db.StringProperty()
	request_key = db.StringProperty()
	reset_password = db.BooleanProperty(default=False)
	created = db.DateTimeProperty(auto_now_add=True)
	activated = db.BooleanProperty(default=False)
	facebook_login = db.BooleanProperty(default=False)
	
	@classmethod
	def get_by_email(cls, email):
		return cls.query(cls.email == email).get()
		
	@classmethod
	def get_user_by_name(cls, username): 
		return db.GqlQuery("Select * from User WHERE username= :1", username).get()
	def get_average_rating(self):
		reviews = TaskPostReview.all().filter("user",self)
		total = 0.0
		for review in reviews:
			total += review.get_total_rating()
		return total/reviews.count() if reviews.count() else 0.0
		
	def get_level(self, experience):
		level = {
			1:60,
			2:180,
			3:360,
			4:600,
			5:900,
			6:1260,
			7:1680,
			8:2160,
			9:2720,
			10:99999999
		}
		for lvl, exp in level.items():
			if experience <= exp:
				return lvl
		return None
	def get_percentage(self, experience):
		level = {
			1:60,
			2:180,
			3:360,
			4:600,
			5:900,
			6:1260,
			7:1680,
			8:2160,
			9:2720,
			10:99999999
		}
		for lvl, exp in level.items():
			if experience <= exp:
				return float(experience)/exp*100.0
		return None
	def get_badges(self):
		return Badge.all().filter("user",self).get()
	@classmethod
	def by_id(cls, uid):
		return User()
	@classmethod
	def email_login(cls, username, pw):
		u = cls.get_user_by_name(username)
		if u and valid_pw(username, pw, u.password):
			return u

SECRET = "Wikier"

def make_salt(length=5):
	return ''.join(random.choice(string.letters) for i in range(length))

def make_pw_hash(name, pw, salt = None):
	if not salt:
		salt = make_salt()
	h = hashlib.sha256(name + pw + salt+ SECRET).hexdigest()
	return '%s,%s' % (salt, h)

def valid_pw(name, password, h):
	salt = h.split(',')[0]
	return h == make_pw_hash(name, password, salt)


class Badge(db.Model):
	user = db.ReferenceProperty(User, collection_name='badges')
	facebook_connected = db.BooleanProperty(default=False) #connected with facebook
	identified = db.BooleanProperty(default=False) #send us an id copy
	background_checked = db.BooleanProperty(default=False) #Done a background check
	phone_verified = db.BooleanProperty(default=False) #Phone number has been verified to the user.
	district_head = db.BooleanProperty(default=False) # At one point has the highest grades in a district
	bronze_medal = db.BooleanProperty(default=False) # Has posted 10 tasks
	silver_medal = db.BooleanProperty(default=False) # Has posted 30 tasks
	gold_medal = db.BooleanProperty(default=False) # Has posted 50 tasks
	bronze_star = db.BooleanProperty(default=False) # Has completed 10 tasks
	silver_star = db.BooleanProperty(default=False) # Has completed 30 tasks
	gold_star = db.BooleanProperty(default=False) # Has completed 50 tasks
	meet_the_mouse = db.BooleanProperty(default=False) #finished a task at disneyland
	nightwalker = db.BooleanProperty(default=False) # has done task after 8pm
	champion = db.BooleanProperty(default=False)  #
	outspoken = db.BooleanProperty(default=False) # talked and asked more than 15 messages at the message board
	explorer = db.BooleanProperty(default=False) # Done task in more than 10 district
	trustworthy = db.BooleanProperty(default=False) #edorsed for positive score for a few times
	#later
	multitasker = db.BooleanProperty(default=False) # accepted more than 3 tasks at a time
	i_m_a_baller = db.BooleanProperty(default=False) #help out at a party, later
	legendary = db.BooleanProperty(default=False) # done many many task already
	def return_badge_list(self):
		return [self.facebook_connected, self.identified, self.background_checked, self.phone_verified]
	def return_new_badge_list(self):
		return [self.facebook_connected, self.identified, self.district_head, 
				self.background_checked, self.phone_verified, 
				self.bronze_medal, self.silver_medal, self.gold_medal, self.bronze_star, 
				self.silver_star, self.gold_star, self.meet_the_mouse,
				self.nightwalker, self.champion, self.outspoken, self.explorer,
				self.legendary]
	

class Business(db.Model):
	businessname = db.StringProperty(required=True)
	logo_img = db.BlobProperty()
	password = db.StringProperty(required=True)
	email_address = db.StringProperty(required=True)
	profile_img = db.BlobProperty()
	introduction = db.TextProperty(default=None)
	experience = db.IntegerProperty(default=0)
	phone_number = db.PhoneNumberProperty(default=None)
	facebook_id = db.StringProperty()
	request_key = db.StringProperty()
	reset_password = db.BooleanProperty(default=False)
	activated = db.BooleanProperty(default=False)
	created = db.DateTimeProperty(auto_now_add=True)
	
	@classmethod
	def get_by_email(cls, email):
		return db.GqlQuery("Select * from Business WHERE email_address= :1", email).get()
		
	@classmethod
	def email_login(cls, email, pw):
		username = email.split("@")[0]
		u = cls.get_by_email(email)
		if u and valid_pw(username, pw, u.password):
			return u
	@classmethod
	def get_by_name(cls, name):
		return db.GqlQuery("Select * from Business Where businessname= :1", name).get()
	
class ClassPost(db.Model):
	business = db.ReferenceProperty(Business, collection_name='classposts')
	preview_img_one = db.BlobProperty()
	title = db.StringProperty()
	price = db.StringProperty()
	description = db.TextProperty(required=True)
	location = db.StringProperty(required=True)
	website = db.StringProperty()
	views = db.FloatProperty()
	purchases = db.FloatProperty()
	rating = db.FloatProperty()
	active = db.BooleanProperty(default=True)
	created = db.DateTimeProperty(auto_now_add=True)
	def render_description(self):
		self._render_text = self.description.replace('\n', '<br>')
		return self._render_text
	def render_row(self):
		return render_str('class-row.html', classpost=self)
	def render(self):
		self._render_text = self.description.replace('\n', '<br>')
		return render_str("class.html", classpost=self)
	def get_key_id(self):
		return ClassPost.user.get_value_for_datastore(self)
	def get_reviews(self):
		return ClassPostReview.all().filter("classpost", self)


class ClassPostReview(db.Model):
	user = db.ReferenceProperty(User)
	classpost = db.ReferenceProperty(ClassPost)
	fun = db.FloatProperty()
	expertise = db.FloatProperty()
	quality = db.FloatProperty()
	professionalism = db.FloatProperty()
	feedback = db.TextProperty()
	created = db.DateTimeProperty(auto_now_add=True)
	def get_reviewer(self):
		return self.classpost.user
	def get_total_rating(self):
		total = (self.fun + self.expertise + self.quality + self.professionalism ) / 4
		return total
	def render_row(self):
		return render_str('review-row.html', classreview=self)


class ClassPostMessage(db.Model):
	classpost = db.ReferenceProperty(ClassPost, collection_name="classpostmessages")
	user = db.ReferenceProperty(User)
	message = db.TextProperty(required=True)
	created = db.DateTimeProperty(auto_now_add=True)
	def get_parent_taskpost(self):
		return self.parent()
	def render_row(self):
		return render_str("message-row.html", classpostmessage=self)

class ClassPurchase(db.Model):
	sid = db.StringProperty()
	payerid = db.StringProperty()
	business = db.ReferenceProperty(Business)
	user = db.ReferenceProperty(User)
	classpost_id = db.StringProperty()
	classpost = db.ReferenceProperty(ClassPost)
	amount = db.StringProperty()
	created = db.DateTimeProperty(auto_now_add=True)
	def get_class_purchase(self, sid):
		return ClassPurchase.all().filter('sid', sid).get()
	def render_row(self):
		return render_str("class-receipt-row.html", ClassPurchase=self)
	

class TaskPost(db.Model):
	user = db.ReferenceProperty(User, collection_name='taskposts')
	acceptance = db.ReferenceProperty(User, default=None)
	title = db.StringProperty(required=True)
	category = db.StringProperty(
		choices=('Delivery', 'Home Improvement', 'Shopping', 'Office Help', 
		'Moving and Packing', 'Virtual Assistance', 'Line Up','Event Help', 'Skilled', 'Recreational','Others'))
	title_url = db.StringProperty()
	payment_method = db.StringProperty(required=True, choices=('Cash','Online'))
	description = db.TextProperty(required=True)
	location = db.StringProperty(required=True)
	funded = db.BooleanProperty(default=False)
	district = db.StringProperty()
	latlng = db.GeoPtProperty()
	price = db.StringProperty()
	spending = db.StringProperty()
	finish_time = db.StringProperty(required=True)
	created = db.DateTimeProperty(auto_now_add=True)
	completed = db.BooleanProperty(default=False)
	reviewed = db.BooleanProperty(default=False)
	def render_row(self):
		return render_str('task-row.html', taskpost=self)
	def render_short_row(self):
		return render_str('task-row-short.html', taskpost=self)
	def render(self):
		self._render_text = self.description.replace('\n', '<br>')
		return render_str("task.html", task=self)
	def render_description(self):
		self._render_text = self.description.replace('\n', '<br>')
		return self._render_text
	def getElementByName(url_name):
		q = db.GqlQuery("SELECT * FROM TaskPost")
	def get_key_id(self):
		return TaskPost.user.get_value_for_datastore(self)
	def addTaskApplication(self, user, message, contact_info="", price=price):
		new_task_app = TaskApplication(taskpost=self, user=user, message=message, contact_info=contact_info, price=price)
		new_task_app.put()
	def getTaskApplication(self):
		return TaskApplication.all().filter('taskpost', self)
	def getAcceptedApplication(self):
		return TaskApplication.all().filter('taskpost', self).filter('user', self.acceptance).get()
	def getTaskPostMessages(self):
		return TaskPostMessage.all().filter('taskpost', self)
	def getUserObject(self):
		return user
	def is_pending_approval(self, current_username):
		taskapplications = TaskApplication.all().filter('taskpost', self)
		for taskapplication in taskapplications:
			if taskapplication.user.username == current_username:
				return True
		return False
	def is_accepted(self):
		return self.acceptance
	def deleteTaskPost(self):
		pass
	def as_dict(self):
		time_fmt = '%c'
		d = {
		'title': self.title,
		'poster': self.user.username,
		'category': self.category,
		'description': self.description,
		'location': self.location,
		'latlng': str(self.latlng),
		'price': self.price,
		'created' : str(self.created.utcnow().strftime("%Y-%m-%d %H:%M:%S %z")),
		'payment_method' : self.payment_method,
		'finish_time' : self.finish_time,
		'funded' : self.funded,
		'completed' : self.completed,
		'accepted' : True if self.acceptance else False,
		'tasker': self.acceptance.username if self.acceptance else ""
		}
		return d


class TaskPostReview(db.Model):
	user = db.ReferenceProperty(User)
	taskpost = db.ReferenceProperty(TaskPost)
	speed = db.FloatProperty()
	expertise = db.FloatProperty()
	quality = db.FloatProperty()
	professionalism = db.FloatProperty()
	responsiveness = db.FloatProperty()
	feedback = db.TextProperty()
	created = db.DateTimeProperty(auto_now_add=True)
	def get_reviewer(self):
		return self.taskpost.user
	def get_total_rating(self):
		total = (self.speed + self.expertise + self.quality + self.professionalism + self.responsiveness) / 5
		return total
	def render_row(self):
		return render_str('review-row.html', taskreview=self)

class TaskApplication(db.Model):
	user = db.ReferenceProperty(User, collection_name='taskapplications')
	taskpost = db.ReferenceProperty(TaskPost)
	contact_info = db.StringProperty()
	price = db.StringProperty()
	message = db.TextProperty()
	created = db.DateTimeProperty(auto_now_add=True)
	def render_row(self, current_username):
		return render_str('application-row.html', application=self, current_username=current_username)
	def get_key_id(self):
		return TaskPost.user.get_value_for_datastore(self)
	def getParentTaskPost(self):
		return self.taskpost
	def getParentId(self):
		return self.taskpost.key().id()
	def get_comments(self):
		return TaskApplicationComments.all().filter("taskapplication", self).order("-created")
	def render_message(self):
		self._render_text = self.message.replace('\n', '<br>')
		return self._render_text
	def find_by_name(self, username):
		if len(username) == 0:
			return None
		#taskapp = self.all().filter('user', User.all().filter("username", username).get()).get()
		return None #taskapp

class TaskPostMessage(db.Model):
	taskpost = db.ReferenceProperty(TaskPost, collection_name="taskpostmessages")
	user = db.ReferenceProperty(User)
	message = db.TextProperty(required=True)
	created = db.DateTimeProperty(auto_now_add=True)
	def get_parent_taskapplication(self):
		return self.parent()
	def render_row(self):
		return render_str("message-row.html", taskpostmessage=self)

class TaskApplicationComments(db.Model):
	taskapplication = db.ReferenceProperty(TaskApplication, collection_name="taskapplicationcomments")
	user = db.ReferenceProperty(User)
	comment = db.TextProperty()
	created = db.DateTimeProperty(auto_now_add=True)
	def get_parent_taskapplication(self):
		return self.parent()
	def render_row(self):
		return render_str("comment-row.html", taskappcomment=self)


class TaskPayment(db.Model):
	sid = db.StringProperty()
	payerid = db.StringProperty()
	user = db.ReferenceProperty(User)
	taskpost = db.ReferenceProperty(TaskPost)
	amount = db.StringProperty()
	created = db.DateTimeProperty(auto_now_add=True)
	def get_task_payment(self, sid):
		return TaskPayment.all().filter('sid', sid).get



class DemoTestCase(unittest.TestCase):
	def setUp(self):
		pass