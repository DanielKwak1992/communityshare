import logging
from datetime import datetime

from sqlalchemy import Column, Integer, Boolean, DateTime, Table, ForeignKey
from sqlalchemy import String, or_, and_
from sqlalchemy.orm import relationship

from community_share.store import Base, session
from community_share.models.base import Serializable

conversation_user_table = Table('conversation_user', Base.metadata,
    Column('conversation_id', Integer, ForeignKey('conversation.id')),
    Column('user_id', Integer, ForeignKey('user.id'))
)

logger = logging.getLogger(__name__)


class Conversation(Base, Serializable):
    __tablename__ = 'conversation'

    MANDATORY_FIELDS = [
        'title', 'search_id', 'userA_id', 'userB_id',
    ]
    WRITEABLE_FIELDS = [
        'title',
    ]
    STANDARD_READABLE_FIELDS = []
    ADMIN_READABLE_FIELDS = [
        'id', 'title', 'search_id', 'userA_id', 'userB_id', 'date_created', 'active'
    ]

    PERMISSIONS = {
        'standard_can_read_many': True
    }    

    id = Column(Integer, primary_key=True)
    active = Column(Boolean, default=True, nullable=False)
    date_created = Column(DateTime, nullable=False, default=datetime.utcnow)
    title = Column(String(200), nullable=False)
    search_id = Column(Integer, ForeignKey('search.id'), nullable=False)
    userA_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    userB_id = Column(Integer, ForeignKey('user.id'), nullable=False)

    messages = relationship('Message', backref='conversation')
    userA = relationship('User', primaryjoin='Conversation.userA_id == User.id')
    userB = relationship('User', primaryjoin='Conversation.userB_id == User.id')

    @classmethod
    def has_add_rights(cls, data, user):
        '''
        A user has rights to add a conversation if they are
        one of the users.
        '''
        has_rights = False
        if ((int(data.get('userA_id', -1)) == user.id ) or
            (int(data.get('userB_id', -1)) == user.id )):
            has_rights = True
        return has_rights

    def has_standard_rights(self, requester):
        has_rights = self.has_admin_rights(requester)
        return has_rights

    def is_in_conversation(self, requester):
        return (requester.id == self.userA_id) or (requester.id == self.userB_id)

    def has_admin_rights(self, requester):
        has_rights = False
        if requester is not None:
            if requester.is_administrator:
                has_rights = True
            else:
                if self.is_in_conversation(requester):
                    has_rights = True
        return has_rights

    def admin_serialize(self):
        d = {}
        for fieldname in self.ADMIN_READABLE_FIELDS:
            d[fieldname] = getattr(self, fieldname)
        d['messages'] = [message.admin_serialize() for message in self.messages]
        d['userA'] = self.userA.standard_serialize()
        d['userB'] = self.userB.standard_serialize()
        return d

    @classmethod
    def args_to_query(cls, args, requester):
        user_id = args.get('user_id_with_unviewed_messages', None)
        logger.debug('user id with unviewed messages is {0}'.format(user_id))
        logger.debug('user id requesting is {0}'.format(user_id))
        try:
            user_id = int(user_id)
            if requester.id == user_id:
                query = session.query(Conversation)
                query = query.filter(
                    or_(Conversation.userA==requester, Conversation.userB==requester))
                query = query.filter(
                    and_(Message.viewed==False, Message.sender_user!=requester))
            else:
                query = None
        except ValueError:
            query = None
        logger.debug('query is {0}'.format(query))
        return query


class Message(Base, Serializable):
    __tablename__ = 'message'

    MANDATORY_FIELDS = [
        'conversation_id', 'sender_user_id', 'content',
    ]
    WRITEABLE_FIELDS = ['viewed']
    STANDARD_READABLE_FIELDS = []
    ADMIN_READABLE_FIELDS = [
        'id', 'conversation_id', 'sender_user_id', 'content', 'date_created', 'viewed'
    ]

    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey('conversation.id'))
    sender_user_id = Column(Integer, ForeignKey('user.id'))
    content = Column(String, nullable=False)
    viewed = Column(Boolean, nullable=False, default=False)
    date_created = Column(DateTime, nullable=False, default=datetime.utcnow)

    sender_user = relationship('User')

    @classmethod
    def has_add_rights(cls, data, user):
        '''
        A user has rights to add a message if the sender_user_id is correct
        and it is to a conversation of which they are a member.
        '''
        has_rights = False
        if int(data.get('sender_user_id', -1)) == user.id:
            conversation_id = data.get('conversation_id', -1)
            conversation = session.query(Conversation).filter(
                Conversation.id==conversation_id).first()
            if (conversation.userA_id == user.id) or (conversation.userB_id == user.id):
                has_rights = True
        return has_rights

    def receiver_user(self):
        if (self.sender_user_id == self.conversation.userA.id):
            receiver_user = self.conversation.userB
        else:
            receiver_user = self.conversation.userA
        return receiver_user

    def has_admin_rights(self, requester):
        has_rights = False
        if requester is not None:
            if requester.is_administrator:
                has_rights = True
            elif requester.id == self.receiver_user().id:
                has_rights = True
        return has_rights
