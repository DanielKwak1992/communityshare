from datetime import datetime, timedelta
import string, json, random

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship, backref

import passlib
from passlib import context

from community_share import settings
from community_share.store import Base

class Serializable(object):
    """
    Doesn't implement a necessary 'get' method.
    """
    
    MANDATORY_FIELDS = []
    WRITEABLE_FIELDS = []
    STANDARD_READABLE_FIELDS = ['id']
    ADMIN_READABLE_FIELDS = ['id']

    PERMISSIONS = {
        'standard_can_ready_many': False
    }

    def standard_serialize(self):
        d = {}
        for fieldname in self.STANDARD_READABLE_FIELDS:
            d[fieldname] = getattr(self, fieldname)
        return d

    def admin_serialize(self):
        d = {}
        for fieldname in self.ADMIN_READABLE_FIELDS:
            d[fieldname] = getattr(self, fieldname)
        return d

    @classmethod
    def admin_deserialize_add(cls, data):
        for fieldname in cls.MANDATORY_FIELDS:
            if not fieldname in data:
                raise Exception('Missing necessary field: {0}'.format(fieldname))
        item = cls()
        for fieldname in data.keys():
            if fieldname in cls.WRITEABLE_FIELDS and hasattr(item, fieldname):
                setattr(item, fieldname, data[fieldname])
        return item

    def admin_deserialize_update(self, data):
        for fieldname in data.keys():
            if fieldname in self.WRITEABLE_FIELDS and hasattr(self, fieldname):
                setattr(self, fieldname, data[fieldname])
            
    @classmethod
    def admin_deserialize(self, data):
        if 'id' in data:
            item = self.get(data['id'])
            item.admin_deserialize_update(data)
        else:
            item = self.admin_deserialize_add(data)
        return item


class Secret(Base):
    __tablename__ = 'secret'
    KEY_LENGTH = 200
    
    key = Column(String(KEY_LENGTH), primary_key=True)
    info = Column(String)
    expiration = Column(DateTime, default=datetime.utcnow)
    used = Column(Boolean, default=False)

    @classmethod
    def make_key(cls):
        chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
        key = ''.join(random.choice(chars) for _ in range(cls.KEY_LENGTH))
        return key

    @classmethod
    def make(cls, info, hours_duration):
        info_as_json = json.dumps(info)
        key = cls.make_key()
        expiration = datetime.now() + timedelta(hours=hours_duration)
        secret = Secret(key=key, info=info_as_json, expiration=expiration)
        return secret

    def get_info(self):
        info = None
        try:
            info = json.loads(self.info)
        except ValueError:
            logger.error("Invalid JSON data in secret.info")
        return info

class AdministratorRole(Base, Serializable):
    __tablename__ = 'administrator_role'
    
    id = Column(Integer, primary_key=True)


class User(Base, Serializable):
    __tablename__ = 'users'

    MANDATORY_FIELDS = ['name', 'email']
    WRITEABLE_FIELDS = ['name']
    STANDARD_READABLE_FIELDS = ['id', 'name', 'is_administrator']
    ADMIN_READABLE_FIELDS = ['id', 'name', 'email' , 'datecreated', 'lastactive', 'is_administrator']
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    email = Column(String(50), nullable=False)
    passwordhash = Column(String(120), nullable=False)
    datecreated = Column(DateTime, nullable=False, default=datetime.utcnow)
    administrator_role_id = Column(Integer, ForeignKey('administrator_role.id')) 
    lastactive = Column(DateTime)

    administrator_role = relationship('AdministratorRole',
                                      backref=backref('user', uselist=False))

    pwd_context = passlib.context.CryptContext(
        schemes=['sha512_crypt'],
        default='sha512_crypt',
        all__vary_rounds = 0.1,
        sha512_crypt__vary_rounds = 8000,
    )

    def is_password_correct(self, password):
        is_correct = self.pwd_context.verify(password, self.passwordhash)
        return is_correct

    def set_password(self, password):
        passwordhash = User.pwd_context.encrypt(password)
        self.passwordhash = passwordhash

    def __repr__(self):
        output = "<User(email={email})>".format(email=self.email) 
        return output

    @property
    def is_administrator(self):
        is_administrator = (self.administrator_role is not None)
        return is_administrator

    def has_admin_rights(self, user):
        has_admin_rights = False
        if user.is_administrator:
            has_admin_rights = True
        elif user.id == self.id:
            has_admin_rights = True
        return has_admin_rights
            

def make_admin_user(name, email, password):
    passwordhash = User.pwd_context.encrypt(password)
    new_user = User(name=name, email=email, passwordhash=passwordhash)
    new_role = AdministratorRole()
    new_user.administrator_role = new_role
    session.add(new_user)
    session.add(new_role)
    session.commit()
    
if __name__ == '__main__':
    make_admin_user('Ben Reynwar', 'ben@reynwar.net', 'viewable')
