from datetime import datetime, timedelta

from flask import render_template, redirect, url_for, abort, flash, request, current_app, session
from flask_babel import lazy_gettext
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from sqlalchemy import func, case, between, and_, or_

from . import main
from .forms import (EditProfileForm, EditProfileAdminForm, TopicForm, TopicGroupForm, TopicWithPollForm,
                    CommentForm, CommentEditForm, MessageReplyForm, MessageSendForm, SearchForm)
from ..app import babel, db
from ..decorators import admin_required, permission_required
from ..models import Permission, Role, User, Topic, TopicGroup, Comment, PollAnswer, Message, Favorite


def get_topic_group(topic_group_id):
    page = request.args.get('page', 1, type=int)
    t_group = TopicGroup.query.filter_by(id=topic_group_id, deleted=False).first_or_404()

    if page == 1 or not current_app.config['TOPIC_GROUPS_ONLY_ON_1ST_PAGE']:
        t_groups = TopicGroup.query.with_entities(
            TopicGroup, func.sum(case([(Topic.deleted == False, 1)], else_=0))).outerjoin(
            Topic, TopicGroup.id == Topic.group_id).filter(
            and_(TopicGroup.deleted == False, TopicGroup.group_id == t_group.id)).group_by(
            TopicGroup.id).order_by(TopicGroup.priority, TopicGroup.created_at.desc()).all()
    else:
        t_groups = []

    pagination = Topic.query.with_entities(
        Topic, User,
        func.sum(case([(Comment.deleted == False, 1)], else_=0)),
        func.max(case([(Comment.deleted == False, Comment.created_at)], else_=None))
        ).join(User, Topic.author_id == User.id).outerjoin(
        Comment, Topic.id == Comment.topic_id).filter(
        and_(Topic.group_id == t_group.id, Topic.deleted == False)).group_by(Topic.id, User.id).order_by(
        Topic.created_at.desc()).paginate(page, per_page=current_app.config['TOPICS_PER_PAGE'], error_out=True)

    return t_group, t_groups, pagination


@main.route('/')
def index():
    t_group, t_groups, pagination = get_topic_group(current_app.config['ROOT_TOPIC_GROUP'])
    return render_template('index.html', topic_group=t_group, topic_groups=t_groups, topics=pagination.items,
                           pagination=pagination)


