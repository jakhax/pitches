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


@main.route('/topic/<int:topic_id>', methods=['GET', 'POST'])
def topic(topic_id):
    tpc = Topic.query.filter_by(id=topic_id, deleted=False).first_or_404()
    

    form = CommentForm(current_user) if current_user.can(Permission.PARTICIPATE) else None
    if form and form.validate_on_submit():
        tpc.add_comment(current_user, form.body.data)
        flash(lazy_gettext('Your comment has been published.'))
        return redirect(url_for('main.topic', topic_id=topic_id, page=-1, _anchor='comment-last'))

    page = request.args.get('page', 1, type=int)
    if page == -1:
        page = max((tpc.comments_count - 1) // current_app.config['COMMENTS_PER_PAGE'] + 1, 1)

    pagination = Comment.query.with_entities(
        Comment, User).join(User, Comment.author_id == User.id).filter(
        and_(Comment.topic_id == tpc.id, Comment.deleted == False)).order_by(
        Comment.created_at.asc()).paginate(page, per_page=current_app.config['COMMENTS_PER_PAGE'], error_out=True)

    user_vote = current_user.get_vote(tpc)
    if tpc.poll and user_vote:
        poll_data = tpc.get_poll_results()
    else:
        poll_data = [(a.id, a.body) for a in tpc.poll_answers.filter_by(deleted=False).all()]

    return render_template('topic.html', topic=tpc,form=form, user_vote=user_vote,
                           poll_data=poll_data, comments=pagination.items, pagination=pagination)


@main.route('/create_topic/<int:topic_group_id>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.WRITE)
def create_topic(topic_group_id):
    t_group = TopicGroup.query.get_or_404(topic_group_id)
    if t_group.protected and not current_user.is_moderator():
        abort(403)

    with_poll = True
    form = TopicForm()
    form.remove_edit_fields()

    if form.submit.data and form.validate_on_submit():
        new_topic = Topic(title=form.title.data, body=form.body.data, group=t_group,
                          author=current_user._get_current_object())
        if with_poll:
            new_topic.poll = form.poll_question
        db.session.add(new_topic)
        db.session.commit()
        if with_poll:
            poll_answers = form.poll_answers.strip().splitlines()
            new_topic.update_poll_answers(poll_answers)
        flash(lazy_gettext('The pitch has been created.'))
        return redirect(url_for('main.topic', topic_id=new_topic.id))

    elif not with_poll and form.add_poll.data:
        if form.title.data or form.body.data:
            if form.validate_on_submit():
                new_topic = Topic(title=form.title.data, body=form.body.data, group=t_group,
                                  author=current_user._get_current_object())
                db.session.add(new_topic)
                db.session.commit()
                flash(lazy_gettext('The pitch has been saved. Fill data for a poll.'))
                return redirect(url_for('main.edit_topic', topic_id=new_topic.id, poll=1))
        else:
            return redirect(url_for('main.create_topic', topic_group_id=topic_group_id, poll=1))

    elif form.cancel.data:
        flash(lazy_gettext('Pitch creation was cancelled.'))
        return redirect(url_for('main.topic_group', topic_group_id=topic_group_id))

    return render_template('create_topic.html', form=form, topic_group=t_group)


@main.route('/edit_topic/<int:topic_id>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.WRITE)
def edit_topic(topic_id):
    tpc = Topic.query.filter_by(id=topic_id, deleted=False).first_or_404()
    if current_user != tpc.author and not current_user.is_moderator():
        abort(403)

    with_poll = request.args.get('poll', 0, type=int) or tpc.poll
    form = TopicWithPollForm() if with_poll else TopicForm()
    if not current_user.is_moderator():
        del form.group_id

    if form.submit.data and form.validate_on_submit():
        if current_user.is_moderator():
            tpc.group_id = form.group_id.data
        tpc.title = form.title.data
        tpc.body = form.body.data
        if with_poll:
            tpc.poll = form.poll_question.data
            tpc.update_poll_answers(form.poll_answers.data.strip().splitlines())
        tpc.updated_at = datetime.utcnow()
        db.session.add(tpc)
        flash(lazy_gettext('The pitch has been updated.'))
        return redirect(url_for('main.topic', topic_id=tpc.id))

    elif not with_poll and form.add_poll.data and form.validate_on_submit():
        if current_user.is_moderator():
            tpc.group_id = form.group_id.data
        tpc.title = form.title.data
        tpc.body = form.body.data
        tpc.updated_at = datetime.utcnow()
        db.session.add(tpc)
        flash(lazy_gettext('The pitch has been saved. Fill data for a poll.'))
        return redirect(url_for('main.edit_topic', topic_id=tpc.id, poll=1))

    elif form.cancel.data:
        flash(lazy_gettext('Pitch editing was cancelled.'))
        return redirect(url_for('main.topic', topic_id=tpc.id))

    elif form.delete.data:
        tpc.comments.update(dict(deleted=True))
        tpc.poll_answers.update(dict(deleted=True))
        tpc.poll_votes.update(dict(deleted=True))
        tpc.deleted = True
        tpc.updated_at = datetime.utcnow()
        db.session.add(tpc)
        flash(lazy_gettext('The pitch has been deleted.'))
        return redirect(url_for('main.topic_group', topic_group_id=tpc.group_id))

    if not form.is_submitted():
        form.title.data = tpc.title
        form.body.data = tpc.body
        if form.group_id:
            form.group_id.data = tpc.group_id
        if tpc.poll:
            form.poll_question.data = tpc.poll
            form.poll_answers.data = '\n'.join([a.body for a in tpc.poll_answers.filter_by(deleted=False).all()])

    return render_template('edit_topic.html', form=form, topic=tpc)


