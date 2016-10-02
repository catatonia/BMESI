from rauth import OAuth2Service
from flask import current_app,url_for,request,redirect,session
import json,urllib2


class OAuthSignIn(object):
	providers = None

	def __init__(self,provider_name):
		self.provider_name = provider_name
		credentials = current_app.config['OAUTH_CREDENTIALS'][provider_name]
		self.client_id = credentials['client_id']
		self.client_secret = credentials['client_secret']

	def authorize(self):
		pass

	def callback(self):
		pass

	def get_callback_url(self):
		return url_for('oauth_callback',provider=self.provider_name,_external=True)

	@classmethod
	def get_provider(self,provider_name):
		if self.providers is None:
			self.providers = {}
			for provider_class in self.__subclasses__():
				provider = provider_class()
				self.providers[provider.provider_name] = provider

		return self.providers[provider_name]



class FacebookSignIn(OAuthSignIn):
	def __init__(self):
		super(FacebookSignIn,self).__init__('facebook')
		self.service = OAuth2Service(
			name='facebook',
			client_id=self.client_id,
			client_secret=self.client_secret,
			authorize_url='https://graph.facebook.com/oauth/authorize',
			access_token_url='https://graph.facebook.com/oauth/access_token',
			base_url='https://graph.facebook.com/'
		)

	def authorize(self):
		return redirect(self.service.get_authorize_url(
			scope='email',
			response_type='code',
			redirect_url=self.get_callback_url())
		)

	def callback(self):
		if 'code' not in request.args:
			return None,None,None
		oauth_session=self.service.get_authorize_session(
			data={'code':request.args['code'],
				  'grant_type':'authorization_code',
				  'redirect_url':self.get_callback_url()
				 }
		)
		me = oauth_session.get('me?fields=id,email').json()
		return(
			'facebook$' + me['id'],
			me.get('email').split('@')[0],
			me.get('email')
		)


class GoogleSignIn(OAuthSignIn):
	def __init__(self):
		super(GoogleSignIn,self).__init__('google')
		googleinfo = urllib2.urlopen('https://accounts.google.com/.well-known/openid-configuration')
		google_params = json.load(googleinfo)
		self.service = OAuth2Service(
			name='google',
			client_id = self.client_id,
			client_secret = self.client_secret,
			authorize_url=google_params.get('authorization_endpoint'),
			base_url=google_params.get('userinfo_endpoint'),
			access_token_url=google_params.get('token_endpoint')
		)

	def authorize(self):
		return redirect(self.service.get_authorize_url(
			scope='email',
			response_type='code',
			redirect_uri=self.get_callback_url())
		)

	def callback(self):
		if 'code' not in request.args:
			return None,None
		
		oauth_session = self.service.get_auth_session(
			data={'code':request.args['code'],
				  'grant_type':'authorization_code',
				  'redirect_uri':self.get_callback_url()

			},
			decoder = json.loads
		)

		me = oauth_session.get('').json()
		return(me['name'],
			   me['email'])
