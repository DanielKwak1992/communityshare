from community_share.models.search import Label, Search
from community_share.models.user import User, Institution
from community_share.models.conversation import Conversation, Message
from community_share.models.secret import Secret
from community_share.models.share import Share, Event
from community_share.store import Base, engine

if __name__ == '__main__':
    Event.__table__.drop(engine)
    Share.__table__.drop(engine)
    Base.metadata.create_all(engine);
    
