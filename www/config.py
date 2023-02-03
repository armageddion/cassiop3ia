import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
	# Flask-WTF extension uses this to protect web forms against Cross-Site Request Forgery or CSRF
	SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'

	# Flask-SQLAlchemy uses this stuff
	# SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
	# 						'sqlite:///' + os.path.join(basedir, 'app.db')
	SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
							'mysql://alfr3d:alfr3d@localhost/cassiop3ia'

	SQLALCHEMY_TRACK_MODIFICATION = False

	# Mail stuff so that admin can get email reports
	MAIL_SERVER = os.environ.get('MAIL_SERVER')
	MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
	MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
	MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
	MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
	ADMINS = ['your-email@example.com']
