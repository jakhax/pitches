import hashlib
from datetime import datetime

import bleach
from flask import current_app
from flask_login import UserMixin, AnonymousUserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from markdown import markdown
from sqlalchemy import func, or_, and_
from werkzeug.security import generate_password_hash, check_password_hash

from .app import db, login_manager
from .config import config


def on_changed_body_set_body_html(target, value, oldvalue, initiator):
    extensions = [
        'markdown.extensions.tables',
        'markdown.extensions.nl2br',
        'markdown.extensions.sane_lists',
        'markdown.extensions.attr_list',
    ]
    html = markdown(value, extensions=extensions, output_format='html')
    clean_html = bleach.clean(html, tags=current_app.config['ALLOWED_TAGS'],
                              attributes=current_app.config['ALLOWED_ATTRIBUTES'], strip=True)
    target.body_html = bleach.linkify(clean_html)


class Permission:
    READ = 0x01
    PARTICIPATE = 0x02
    WRITE = 0x04
    MODERATE = 0x08
    ADMINISTER = 0x80


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    @staticmethod
    def insert_roles():
        roles = {
            'Guest': (Permission.READ, False),
            'Participant': (Permission.READ | Permission.PARTICIPATE, False),
            'User': (Permission.READ | Permission.PARTICIPATE | Permission.WRITE, True),
            'Moderator': (Permission.READ | Permission.PARTICIPATE | Permission.WRITE | Permission.MODERATE, False),
            'Administrator': (0xff, False)
        }
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role %r>' % self.name




class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(32))
    username_normalized = db.Column(db.String(32), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    topics = db.relationship('Topic', backref='author', lazy='dynamic')
    topic_groups = db.relationship('TopicGroup', backref='author', lazy='dynamic')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')
    poll_votes = db.relationship('PollVote', backref='author', lazy='dynamic')
    sent_messages = db.relationship('Message', foreign_keys=[Message.author_id], backref='author', lazy='dynamic')
    received_messages = db.relationship('Message', foreign_keys=[Message.receiver_id], backref='receiver',
                                        lazy='dynamic')
    favorite_topics = db.relationship('Topic', secondary='favorites', lazy='dynamic')

    # Profile:
    name = db.Column(db.String(64))
    homeland = db.Column(db.String(64))
    about = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=func.now())
    updated_at = db.Column(db.DateTime, default=func.now())
    last_seen = db.Column(db.DateTime, default=func.now())
    avatar = db.Column(db.String(256))

    def __init__(self, *args, **kwargs):
        super(User, self).__init__(*args, **kwargs)
        if self.role is None:
            if self.email == current_app.config['APP_ADMIN']:
                self.role = Role.query.filter_by(permissions=0xff).first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
        if self.avatar is None and self.email is not None:
            self.avatar = self.gravatar()

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_token(self, expiration=3600, **kwargs):
        s = Serializer(current_app.secret_key, expiration)
        data = {'user_id': self.id}
        data.update(kwargs)
        return s.dumps(data)

    def confirm_token(self, token):
        s = Serializer(current_app.secret_key)
        try:
            data = s.loads(token)
        except:
            return False, None
        if data.get('user_id') != self.id:
            return False, data
        return True, data

    def confirm_registration(self, token):
        result, _ = self.confirm_token(token)
        if not result:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def confirm_new_email(self, token):
        result, data = self.confirm_token(token)
        if not result:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        db.session.add(self)
        return True

    def confirm_reset(self, token, new_password):
        result, _ = self.confirm_token(token)
        if not result:
            return False
        self.password = new_password
        db.session.add(self)
        return True

    def can(self, permissions):
        return self.role is not None and (self.role.permissions & permissions) == permissions

    def is_administrator(self):
        return self.can(Permission.ADMINISTER)

    def is_moderator(self):
        return self.can(Permission.MODERATE)

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    def gravatar(self, size=256, default='identicon', rating='g'):
        hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=current_app.config['BASE_GRAVATAR_URL'], hash=hash, size=size, default=default, rating=rating)

    def get_vote(self, topic):
        vote = PollAnswer.query.with_entities(PollAnswer.body, PollVote.id).join(
            PollVote, PollAnswer.id == PollVote.poll_answer_id).filter(
            and_(PollAnswer.topic_id == topic.id, PollVote.author_id == self.id)).first()
        return vote

    def get_unread_messages_count(self):
        return db.session.query(func.count(Message.id)).filter(
            and_(Message.receiver_id == self.id, Message.unread == True, Message.receiver_deleted == False,)).scalar()

    def __repr__(self):
        return '<User %r>' % self.username


class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False

    def is_moderator(self):
        return False

    def get_vote(self, topic):
        return False


login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


