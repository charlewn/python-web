from controllers import Handler
from models import Models
import logging
from google.appengine.api import memcache
from google.appengine.api import urlfetch
from lib import utils
import urllib2
import urllib
import cgi


PP_URL = "https://www.paypal.com/cgi-bin/webscr"
PP_SANDBOX_URL = "https://www.paypal.com/webscr?cmd=_express-checkout&token="
ACCOUNT_EMAIL = "foonlife@gmail.com"
SANDBOX_ACCOUNT_EMAIL = "foonlife-facilitator@gmail.com"

API_URL = 'https://api-3t.paypal.com/nvp'
SANDBOX_API_URL = "https://api-3t.sandbox.paypal.com/nvp"
ADD_NVP_PARAMS = { 

    # 3 Token Credentials
    'USER' : 'foonlife_api1.gmail.com',
    'PWD' : 'GXH3F6ZT7R7SEKGP',
    'SIGNATURE' : 'ADwCenzdh3svFyQtpwkS0Qhn4sSZA3wUDEiitineHLX4KXyCa9-E4Wx3',
    # API Version
    'VERSION' : '82.0'
}   

SANDBOX_ADD_NVP_PARAMS = {
	# 3 Token Credentials
    'USER' : 'foonlife-facilitator_api1.gmail.com',
    'PWD' : '1365343946',
    'SIGNATURE' : 'AQU0e5vuZCvSg-XJploSa.sGUDlpAcJLj99Nn6CgDExvyN5-iAS3J4wy',
    # API Version
    'VERSION' : '82.0'
}
adaptive_headers = {
    'X-PAYPAL-SECURITY-USERID' : 'XXX',
    'X-PAYPAL-SECURITY-PASSWORD' : 'XXX',
    'X-PAYPAL-SECURITY-SIGNATURE' : 'XXX',
    'X-PAYPAL-REQUEST-DATA-FORMAT' : 'JSON',
    'X-PAYPAL-RESPONSE-DATA-FORMAT' : 'JSON',
    'X-PAYPAL-APPLICATION-ID' : 'APP-80W284485P519543T' # Sandbox
}

seller_email = 'foonlife@gmail.com'


class ProceedToPaymentHandler(Handler.Handler):
	def get(self, task_id):
		params = {}
		cache_taskpost = utils.single_task_cache(task_id)
		username = self.request.cookies.get("username").split("|")[0]
		if cache_taskpost.completed == True or username != cache_taskpost.user.username:
			self.redirect("/task/%s" % task_id)
			return
		params["taskpost"] = cache_taskpost
		amount = int(cache_taskpost.price) + int(cache_taskpost.spending)
		params["post_amount"] = cache_taskpost.getAcceptedApplication().price
		params["task_number"] = task_id
		self.render_form_login_required("task-payment.html", template_values=params)
	def post(self):
		pass


class PurchaseCreditsHandler(Handler.Handler):
	def get(self):
		#for debugging successful page
		#task_id = "5402067753030909952"
		#self.render("successful-purchase.html", task_id=task_id)
		#return
		username = self.request.cookies.get("username").split("|")[0]
		a_User = Models.User.all().filter("username =", username).get()
		params = {}
		if a_User:
			email_address = a_User.email_address
			params["email_address"] = email_address
			params["User"] = a_User
			params["current_username"] = username
		else:
			self.redirect("/")
			return
		self.render_form_login_required("purchase-page.html", template_values=params)
	def post(self):
		pass
		

class PaymentSuccessPageHandler(Handler.Handler):
	def get(self):
		params = {}
		params["task_id"] = self.request.get("task_id")
		self.render_form_login_required("successful-purchase.html", template_values=params)
	def post(self):
		pass


class PaymentHandler(Handler.Handler):
	def post(self, mode=""):
		if mode == "set_ec":
			sid = self.request.cookies.get("username").split("|")[1]
			
			quantity = 1
			task_id = self.request.get("taskid")
			logging.info("task_id: %s" % task_id)
			
			product = "Service Fee"
			price = self.request.get("price")
			amount = price * int(quantity)
			task_id_price = task_id+"|"+ price
			self.set_taskid_cookie(task_id_price)
			#logging.info("amount %s" % amount)
			nvp_params = {
				'L_PAYMENTREQUEST_0_NAME0' : product,
				'L_PAYMENTREQUEST_0_QTY0' : quantity,
				'L_PAYMENTREQUEST_0_AMT0' : str(price),
				'L_PAYMENTREQUEST_0_ITEMCATEGORY0' : 'Physical',
				'PAYMENTREQUEST_0_CURRENCYCODE': 'HKD',
				'PAYMENTREQUEST_0_ITEMAMT' : str(amount),
				'PAYMENTREQUEST_0_AMT' : str(amount),
				'RETURNURL' : self.request.host_url+"/do_ec_payment?sid="+sid,
				'CANCELURL': self.request.host_url+"/cancel_ec?sid="+sid
			}
			#self.write(nvp_params)
			#return
			response = ExpressCheckout.set_express_checkout(nvp_params)
			
			if response.status_code != 200:
				logging.info("Failure for SetExpress Checkout")
				
				template_values = {
					'title' : 'Error',
					'operation' : 'SetExpressCheckout'
				}
				
				return self.write(template_values)
				
				#return self.render_form_login_required("unknown-error.html", template_values=template_values)
				
			# The remainder of the transaction is completed in context
			
			parsed_qs = cgi.parse_qs(response.content)
			
			#logging.info(parsed_qs)
			#self.write(parsed_qs)
			#return
			redirect_url = ExpressCheckout.generate_express_checkout_redirect_url(parsed_qs['TOKEN'][0])
			
			return self.redirect(redirect_url)
				
		else:
			logging.error("Unknown mode for POST request!")
	def get(self, mode=""):
		if mode == "do_ec_payment":
			sid = self.request.get('sid')
			payerid = self.request.get("PayerID")
			
			task_id_price = self.request.cookies.get("taskid")
			
			#logging.info("task_id_price: %s" % task_id_price)
			task_id, price = task_id_price.split("|")[0], task_id_price.split("|")[1]
			
			#logging.info("task_id: %s" % task_id)
			
			quantity = 1
			product = "Service Fee"
			#price = self.request.get("price")
			#logging.info("price %s" % price)
			amount = price
			
			nvp_params = { 
				'PAYERID' : payerid, 
				'PAYMENTREQUEST_0_CURRENCYCODE': 'HKD',
				'PAYMENTREQUEST_0_AMT' : str(amount)
			}
			
			response = ExpressCheckout.do_express_checkout_payment(
						self.request.get("token"), nvp_params)
			#logging.info("response %s" % response)
			if response.status_code != 200:
				#logging.error("Failure for DoExpressCheckoutPayment")
				template_values = {
					'title' : 'Error',
					'operation' : 'DoExpressCheckoutPayment'
				}
				logging.info("Unsuccessful Operations")
				return self.write("Unsuccessful Operations")
			
			parsed_qs = cgi.parse_qs(response.content)
			#logging.info(parsed_qs)
			if parsed_qs['ACK'][0] != 'Success':
				logging.error("Unsuccessful DoExpressCheckoutPayment")
				
				template_values = {
					'title' : 'Error',
					'details' : parsed_qs['L_LONGMESSAGE0'][0]
				}
				logging.error(template_values)
				return
			
			template_values = {
				'title' : 'Successful Payment',
			}
			
			#credit payment
			username = self.request.cookies.get("username").split('|')[0]
			a_User = Models.User.get_user_by_name(username)
			
			a_TP = Models.TaskPayment(sid=sid,user=a_User,amount=amount)
			a_TP.put()
			
			#taskpost complete logic
			#task_id = self.request.cookies.get("taskid")
			a_task = Models.TaskPost.get_by_id(int(task_id))
			a_task.funded = True
			
			a_task.put()
			a_User.put()
			
			#updating the cache
			utils.single_user_cache(a_User.key().id(), update=True)
			utils.single_user_cache_by_name(a_User.username, update=True)
			utils.single_task_cache(task_id, update=True)
			utils.all_task_cache(update=True)
			#logging.info("task id: %s" % task_id)
			#self.redirect("/task/%s/complete/" % task_id)
			self.redirect("/success-payment?task_id=%s" % task_id)
			return
			#self.write("payment succeeded!")
			
		elif mode == "get_ec_details":
			response = ExpressCheckout.generate_express_checkout_redirect_url(self.request.get("token"))
			#self.write(response.status_code)
			#return
			if response.status_code != 200:
				logging.error("Failure for GetExpressCheckoutDetails")
				template_values = {
					'title' : 'Error',
					'operation' : 'GetExpressCheckoutDetails'
				}
				
				self.write("Error")
				
			product = "Service Fee"
			parsed_qs = cgi.parse_qs(response.content)
			
			template_values = {
				'title' : 'Confirm Purchase',
				'quantity' : 1,
				#'email' : parsed_qs['EMAIL'][0],
				'amount' : parsed_qs['PAYMENTREQUEST_0_AMT'][0],
				'query_string_params' : self.request.query_string 
			}
			#self.render_form_login_required("confirm-purchase.html", template_values=template_values)
				
		elif mode == "cancel_ec":
			template_values = {
				'title': 'Cancel Purchase'
			}
			task_id = self.request.cookies.get("taskid")
			self.render("/cancel-purchase.html", task_id=task_id)
		

def _api_call(nvp_params):
	
	params = nvp_params.copy() #copy to avoid mutating nvp_params with update()
	
	params.update(ADD_NVP_PARAMS) # update with 3 token credentials and api version
	#PP_SANDBOX_URL
	response = urlfetch.fetch(API_URL,
							payload=urllib.urlencode(params),
							method=urlfetch.POST,
							validate_certificate=True,
							deadline=10 # seconds
							)
	logging.info("see the content: %s and status_code %s" % (response.content, response.status_code))
	
	if response.status_code != 200:
		decoded_url = cgi.parse_qs(response.content)
		
		for (k,v) in decoded_url.items():
			logging.info('%s=%s' % (k,v[0],))
		
		raise Exception(str(response.status_code))
	
	return response

class ExpressCheckout(object):
	@staticmethod
	def set_express_checkout(nvp_params):
		nvp_params.update(METHOD='SetExpressCheckout')
		return _api_call(nvp_params)
	
	@staticmethod
	def get_express_checkout_details(token):
		nvp_params = { 'METHOD' : 'GetExpressCheckoutDetails', 'TOKEN': token }
		return _api_call(nvp_params)
		
	@staticmethod
	def do_express_checkout_payment(token, nvp_params):
		nvp_params.update(METHOD='DoExpressCheckoutPayment', TOKEN=token)
		return _api_call(nvp_params)
		
	@staticmethod
	def generate_express_checkout_redirect_url(token):
		return "https://www.paypal.com/webscr?cmd=_express-checkout&token=%s" % (token,)
	
	@staticmethod
	def generate_express_checkout_digital_goods_redirect_url(token, commit=True):
		if commit:
			return "https://www.paypal.com/incontext?token=%s&useraction=commit" % (token,)
		else:
			return "https://www.paypal.com/incontext?token=%s" % (token,)
		


"""
class PaymentHandler(Handler.Handler):
	def post(self, mode=""):
		if mode == "set_ec":
			sid = self.request.cookies.get("username").split("|")[1]
			
			quantity = self.request.get("quantity")
			if len(quantity) == 0:
				self.render("cancel-purchase.html")
				return
				
				
			self.set_quantity_cookie(quantity)
			product = "credits"
			price = 0.2
			amount = price * int(quantity)
			#logging.info("amount %s" % amount)
			nvp_params = {
				'L_PAYMENTREQUEST_0_NAME0' : str(quantity) + ' ' + product,
				'L_PAYMENTREQUEST_0_QTY0' : quantity,
				'L_PAYMENTREQUEST_0_AMT0' : str(price),
				'L_PAYMENTREQUEST_0_ITEMCATEGORY0' : 'Digital',
				'PAYMENTREQUEST_0_CURRENCYCODE': 'HKD',
				'PAYMENTREQUEST_0_ITEMAMT' : str(amount),
				'PAYMENTREQUEST_0_AMT' : str(amount),
				'RETURNURL' : self.request.host_url+"/do_ec_payment?sid="+sid,
				'CANCELURL': self.request.host_url+"/cancel_ec?sid="+sid
			}
			#self.write(nvp_params)
			#return
			response = ExpressCheckout.set_express_checkout(nvp_params)
			
			if response.status_code != 200:
				logging.info("Failure for SetExpress Checkout")
				
				template_values = {
					'title' : 'Error',
					'operation' : 'SetExpressCheckout'
				}
				
				return self.write(template_values)
				
				#return self.render_form_login_required("unknown-error.html", template_values=template_values)
				
			# The remainder of the transaction is completed in context
			
			parsed_qs = cgi.parse_qs(response.content)
			
			#logging.info(parsed_qs)
			#self.write(parsed_qs)
			#return
			redirect_url = ExpressCheckout.generate_express_checkout_digital_goods_redirect_url(parsed_qs['TOKEN'][0])
			
			return self.redirect(redirect_url)
				
		else:
			logging.error("Unknown mode for POST request!")
	def get(self, mode=""):
		if mode == "do_ec_payment":
			sid = self.request.cookies.get('sid')
			payerid = self.request.get("PayerID")
			quantity = self.request.cookies.get('qp')
			logging.info("quantity %s" % quantity)
			product = "credits"
			price = 0.2
			amount = int(quantity) * price
			
			nvp_params = { 
				'PAYERID' : payerid, 
				'PAYMENTREQUEST_0_CURRENCYCODE': 'HKD',
				'PAYMENTREQUEST_0_AMT' : str(amount)
			}
			
			response = ExpressCheckout.do_express_checkout_payment(
						self.request.get("token"), nvp_params)
			#logging.info("response %s" % response)
			if response.status_code != 200:
				#logging.error("Failure for DoExpressCheckoutPayment")
				template_values = {
					'title' : 'Error',
					'operation' : 'DoExpressCheckoutPayment'
				}
				logging.info("Unsuccessful Operations")
				return self.write("Unsuccessful Operations")
			
			parsed_qs = cgi.parse_qs(response.content)
			logging.info(parsed_qs)
			if parsed_qs['ACK'][0] != 'Success':
				logging.error("Unsuccessful DoExpressCheckoutPayment")
				
				template_values = {
					'title' : 'Error',
					'details' : parsed_qs['L_LONGMESSAGE0'][0]
				}
				
			template_values = {
				'title' : 'Successful Payment',
			}
			
			#credit payment
			username = self.request.cookies.get("username").split('|')[0]
			a_User = Models.User.get_user_by_name(username)
			quantity = int(quantity)
			a_CP = Models.CreditsPurchase(sid=sid,user=a_User,quantity=quantity)
			a_CP.put()
			if quantity == 300:
				quantity = quantity + 100
			elif quantity == 500:
				quantity = quantity + 200
			elif quantity == 1000:
				quantity = quantity + 300
			
			a_User.credits += quantity
			a_User.experience += 15
			
			a_User.put()
			utils.single_user_cache(a_User.key().id(), update=True)
			utils.single_user_cache_by_name(a_User.username, update=True)
			self.render("/cancel-purchase.html")
			self.write("payment succeeded!")
			
		elif mode == "get_ec_details":
			response = ExpressCheckout.get_express_checkout_details(self.request.get("token"))
			#self.write(response.status_code)
			#return
			if response.status_code != 200:
				logging.error("Failure for GetExpressCheckoutDetails")
				template_values = {
					'title' : 'Error',
					'operation' : 'GetExpressCheckoutDetails'
				}
				
				self.write("Error")
				
			product = "credits"
			parsed_qs = cgi.parse_qs(response.content)
			
			template_values = {
				'title' : 'Confirm Purchase',
				'quantity' : 1,
				#'email' : parsed_qs['EMAIL'][0],
				'amount' : parsed_qs['PAYMENTREQUEST_0_AMT'][0],
				'query_string_params' : self.request.query_string 
			}
			#self.render_form_login_required("confirm-purchase.html", template_values=template_values)
				
		elif mode == "cancel_ec":
			template_values = {
				'title': 'Cancel Purchase'
			}
			self.render("/cancel-purchase.html")


"""