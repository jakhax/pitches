import os,hashlib
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', str(hashlib.sha256('<hard-to-guess-string>').hexdigest().decode()))
    SESSION_PROTECTION = 'basic'
    THEME = os.environ.get('THEME', 'gray')
    SSL_REDIRECT = bool(os.environ.get('SSL_REDIRECT', ''))

    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MQ_USER = os.environ.get('MQ_USER', 'guest')
    MQ_PASSWORD = os.environ.get('MQ_PASSWORD', 'password')
    MQ_HOST = os.environ.get('MQ_HOST', 'mq')
    MQ_PORT = os.environ.get('MQ_PORT', '5672')
    MQ_VHOST = os.environ.get('MQ_VHOST', 'forum')
    AMQP_URL = 'amqp://{user}:{password}@{hostname}:{port}/{vhost}'.format(
        user=MQ_USER, password=MQ_PASSWORD, hostname=MQ_HOST, port=MQ_PORT, vhost=MQ_VHOST
    )
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL',
                                       os.environ.get('RABBITMQ_BIGWIG_URL', AMQP_URL))

    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'pitches@example.com')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'password')

    APP_MAIL_SUBJECT_PREFIX = '[pitches]'
    APP_MAIL_SENDER = 'pitches Admin <name@example.com>'
    APP_ADMIN = os.environ.get('ADMIN_MAIL_USERNAME', 'pitches.admin@example.com')

    BASE_GRAVATAR_URL = 'https://secure.gravatar.com/avatar'
    TOPIC_GROUP_PRIORITY = range(1, 11)
    TOPICS_PER_PAGE = 20
    COMMENTS_PER_PAGE = 20
    MESSAGES_PER_PAGE = 20
    USERS_PER_PAGE = 20
    ROOT_TOPIC_GROUP = 0
    IS_PROTECTED_ROOT_TOPIC_GROUP = True
    TOPIC_GROUPS_ONLY_ON_1ST_PAGE = True

    ALLOWED_TAGS = [
        'a', 'abbr', 'acronym', 'b', 'blockquote', 'br', 'code', 'dd', 'del', 'details', 'dl', 'dt', 'em', 'h1', 'h2',
        'h3', 'h4', 'h5', 'h6', 'h7', 'h8', 'hr', 'i', 'img', 'ins', 'kbd', 'li', 'ol', 'p', 'pre', 'q', 'rp', 'rt',
        'ruby', 's', 'samp', 'strike', 'strong', 'sub', 'summary', 'sup', 'table', 'tbody', 'td', 'tfoot', 'th',
        'thead', 'tr', 'tt', 'ul', 'var'
    ]
    ALLOWED_ATTRIBUTES = {
        'a': ['href', 'title'],
        'abbr': ['title'],
        'acronym': ['title'],
        'img': ['alt', 'src', 'width', 'height'],
    }

    SUPPORTED_LANGUAGES = {'en': 'English', 'ru': 'Russian'}
    BABEL_DEFAULT_LOCALE = 'ru'
    BABEL_DEFAULT_TIMEZONE = 'Europe/Minsk'
    BABEL_TRANSLATION_DIRECTORIES = 'translations'

    @staticmethod
    def init_app(app):
        pass

class DevConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', "postgres+psycopg2://n1ght0wl:1234@localhost/pitches")
    DEBUG = True
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    TESTING = True


class ProdConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "postgres+psycopg2://n1ght0wl:1234@localhost/pitches")
    DEBUG = False
    TESTING = False
    DEBUG_TB_INTERCEPT_REDIRECTS = False

config_options = {
'development':DevConfig,
'production':ProdConfig,
'default':DevConfig
}

config = ProdConfig()
