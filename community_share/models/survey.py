from datetime import datetime
import logging

from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy import ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship

from community_share import Base
from community_share.models.base import Serializable


logger = logging.getLogger(__name__)

class Question(Base, Serializable):
    __tablename__ = 'question'

    MANDATORY_FIELDS = ['text', 'question_type', 'public']
    WRITEABLE_FIELDS = ['public', 'order', 'only_suggested_answers', 'suggested_answers']
    STANDARD_READABLE_FIELDS = [
        'id', 'text', 'question_type', 'public', 'only_suggested_answers', 'order',
        'suggested_answers']
    ADMIN_READABLE_FIELDS = [
        'id', 'text', 'creator', 'date_created', 'question_type', 'public',
        'only_suggested_answers', 'order', 'suggested_answers']
    
    id = Column(Integer, primary_key=True)
    text = Column(String, nullable=True)
    creator_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    active = Column(Boolean, nullable=False, default=True)
    date_created = Column(DateTime, nullable=False, default=datetime.utcnow)
    question_type = Column(String(50), nullable=False)
    public = Column(Boolean, nullable=False)
    only_suggested_answers = Column(Boolean, nullable=False, default=False)
    requires_share_id = Column(Boolean, nullable=False, default=False)
    requires_event_id = Column(Boolean, nullable=False, default=False)
    requires_user_id = Column(Boolean, nullable=False, default=False)
    order = Column(Integer)

    creator = relationship('User')
    suggested_answers = relationship('SuggestedAnswer')

    PERMISSIONS = {
        'all_can_read_many': True,
        'standard_can_read_many': True
    }

    def has_standard_rights(self, requester):
        return True
    
    def serialize_suggested_answers(self):
        serialized = [sa.text for sa in self.suggested_answers if sa.active]
        return serialized

    @classmethod
    def args_to_query(cls, args, requester=None):
        query = cls._args_to_query(args, requester)
        query = query.order_by(cls.order)
        return query

    custom_serializers = {
        'suggested_answers': {
            'standard': serialize_suggested_answers,
            'admin': serialize_suggested_answers,
        }
    }


class SuggestedAnswer(Base, Serializable):
    __tablename__ = 'suggested_answer'

    id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey('question.id'), nullable=False)
    creator_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    text = Column(String)
    active = Column(Boolean, nullable=False, default=True)
    date_created = Column(DateTime, nullable=False, default=datetime.utcnow)

    creator = relationship('User')
    question = relationship('Question')


class Answer(Base, Serializable):
    __tablename__ = 'answer'

    MANDATORY_FIELDS = ['question_id', 'responder_id', 'text']
    WRITEABLE_FIELDS = ['text']
    STANDARD_READABLE_FIELDS = [
        'id', 'question_id', 'responder_id', 'text', 'date_created',
        'about_user_id', 'about_share_id', 'about_event_id']
    ADMIN_READABLE_FIELDS = [
        'id', 'question_id', 'responder_id', 'text', 'date_created',
        'about_user_id', 'about_share_id', 'about_event_id']

    PERMISSIONS = {
        'all_can_read_many': True,
        'standard_can_read_many': True
    }

    id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey('question.id'), nullable=False)
    responder_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    text = Column(String)
    active = Column(Boolean, default=True)
    date_created = Column(DateTime, nullable=False, default=datetime.utcnow)
    about_user_id = Column(Integer, ForeignKey('user.id'), nullable=True)
    about_share_id = Column(Integer, ForeignKey('share.id'), nullable=True)
    about_event_id = Column(Integer, ForeignKey('event.id'), nullable=True)

    question = relationship('Question')

    @classmethod
    def has_add_rights(cls, data, requester):
        data['responder_id'] = int(data.get('responder_id', requester.id))
        if (requester is not None and requester.is_administrator):
            has_rights = True
        elif data['responder_id'] == requester.id:
            has_rights = True
        else:
            has_rights = False
        return has_rights
            
    def has_standard_rights(self, requester):
        has_rights = False
        if requester is not None:
            if requester.is_administrator:
                has_rights = True
            elif self.question.public:
                has_rights = True
            elif self.responder_id == requester.id:
                has_rights = True
        return has_rights

    def has_admin_rights(self, requester):
        has_rights = False
        if requester is not None:
            if requester.is_administrator:
                has_rights = True
            elif self.responder_id == requester.id:
                has_rights = True
        return has_rights
