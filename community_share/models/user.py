from datetime import datetime
import logging

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship, backref

import passlib
from passlib import context

from community_share.store import Base, session
from community_share.models.base import Serializable
from community_share.models.secret import Secret
from community_share.models.search import Search

logger = logging.getLogger(__name__)

class User(Base, Serializable):
    __tablename__ = 'user'

    MANDATORY_FIELDS = ['name', 'email']
    WRITEABLE_FIELDS = ['name', 'is_administrator']
    STANDARD_READABLE_FIELDS = ['id', 'name', 'is_administrator', 'last_active', 'is_educator',
                                'is_community_partner']
    ADMIN_READABLE_FIELDS = ['id', 'name', 'email' , 'date_created', 'last_active',
                             'is_administrator', 'is_educator', 'is_community_partner']
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    email = Column(String(50), nullable=False, unique=True)
    password_hash = Column(String(120), nullable=True)
    date_created = Column(DateTime, nullable=False, default=datetime.utcnow)
    is_administrator = Column(Boolean, nullable=False, default=False) 
    last_active = Column(DateTime)

    pwd_context = passlib.context.CryptContext(
        schemes=['sha512_crypt'],
        default='sha512_crypt',
        all__vary_rounds = 0.1,
        sha512_crypt__vary_rounds = 8000,
    )
    
    def searches_as(self, role):
        searches = session.query(Search).filter_by(
            searcher_user_id=self.id, searcher_role=role).all()
        return searches
        
    @property
    def is_educator(self):
        output = (len(self.searches_as('educator')) > 0)
        return output

    @property
    def is_community_partner(self):
        output = (len(self.searches_as('partner')) > 0)
        return output

    def is_password_correct(self, password):
        if not self.password_hash:
            is_correct = False
        else:
            is_correct = self.pwd_context.verify(password, self.password_hash)
        return is_correct

    def set_password(self, password):
        password_hash = User.pwd_context.encrypt(password)
        self.password_hash = password_hash

    def __repr__(self):
        output = "<User(email={email})>".format(email=self.email) 
        return output

    @classmethod
    def has_add_rights(cls, data, user):
        return False

    def has_admin_rights(self, user):
        has_admin_rights = False
        if user is not None:
            if user.is_administrator:
                has_admin_rights = True
            elif user.id == self.id:
                has_admin_rights = True
        return has_admin_rights
            
    def make_api_key(self):
        secret_data = {
            'userId': self.id,
            'action': 'api_key',
        }
        secret = Secret.create_secret(info=secret_data, hours_duration=24)
        return secret
        
    @classmethod
    def from_api_key(self, key):
        secret = Secret.lookup_secret(key)
        logger.debug('key is {0}'.format(key))
        logger.debug('secret is {0}'.format(secret))
        user_id = None
        if secret is not None:
            info = secret.get_info()
            if info.get('action', None) == 'api_key':
                user_id = info.get('userId', None)
        if user_id is not None:
            user = session.query(User).filter_by(id=user_id).first()
            logger.debug('user from api_key is {0}'.format(user))
        else:
            user = None
        return user

        
