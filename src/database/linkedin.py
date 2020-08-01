import datetime
from sqlalchemy import create_engine
from sqlalchemy import Column, String, Boolean, DateTime, Date, Time, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

from database.credentials import username, password, host, port

engine = create_engine(f'mysql+pymysql://{username}:{password}@{host}:{port}/social', pool_recycle=3600)
session = sessionmaker(bind=engine)()

Base = declarative_base()

class Client(Base):
    """Someone that is paying us money to automate some of their accounts"""

    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, autoincrement=True)
    linkedin_account_id = Column(Integer, ForeignKey("linkedin_accounts.id"))
    name = Column(String)
    email = Column(String)
    phone = Column(String)
    tester = Column(Boolean, default=False)

    # -- ORM --------------------------
    linkedin_account = relationship("LinkedInAccount", uselist=False, back_populates="client")

class LinkedInAccount(Base):
    """A LinkedIn account belonging to one of our clients."""

    __tablename__ = "linkedin_accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True)
    username = Column(String)
    password = Column(String)
    flagged_as_bot_date = Column(DateTime, default=None)
    flagged_as_bot = Column(Integer, default=0)
    tester = Column(Boolean, default=False)

    # -- ORM --------------------------
    client = relationship("Client", uselist=False, back_populates="linkedin_account")
    connections = relationship("LinkedInConnection", uselist=True, back_populates="account")
    messages = relationship("LinkedInMessage", uselist=True, back_populates="account")
    message_templates = relationship("LinkedInMessageTemplate", uselist=True, back_populates="account")
    daily_activity = relationship("LinkedInAccountDailyActivity", uselist=True, back_populates="account")

class LinkedInAccountDailyActivity(Base):
    """Keeps track of a single LinkedIn account's daily activity."""

    __tablename__ = "linkedin_accounts_daily_activity"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey('linkedin_accounts.id'))
    date = Column(Date)
    message_count = Column(Integer, default=0)
    connection_request_count = Column(Integer, default=0)
    activity_limit = Column(Integer, default=10)
    last_activity = Column(DateTime, default=None)

    # -- ORM --------------------------
    account = relationship("LinkedInAccount", uselist=False, back_populates="daily_activity")

class LinkedInConnection(Base):
    """LinkedIn Connections belonging to our clients (connections mutual to multiple clients will be duplicated)"""

    __tablename__ = "linkedin_connections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey('linkedin_accounts.id'))
    name = Column(String)
    url = Column(String, default="")
    location = Column(String, default="")
    position = Column(String, default="")

    # -- ORM --------------------------
    account = relationship("LinkedInAccount", uselist=False, back_populates="connections")
    messages = relationship("LinkedInMessage", uselist=True, back_populates="recipient")

class LinkedInMessageTemplate(Base):
    """Message templates for LinkedIn that will be blasted out to our connections"""

    __tablename__ = "linkedin_message_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey('linkedin_accounts.id'))
    message_template = Column(String, unique=True)
    crc = Column(Integer)
    date_created = Column(DateTime, default=datetime.datetime.utcnow)

    # -- ORM --------------------------
    account = relationship("LinkedInAccount", uselist=False, back_populates="message_templates")
    instances = relationship("LinkedInMessage", uselist=True, back_populates="template")

class LinkedInMessage(Base):
    """Instances of the Message templates that we actually sent to connections."""

    __tablename__ = "linkedin_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey('linkedin_accounts.id'))
    template_id = Column(Integer, ForeignKey('linkedin_message_templates.id'))
    recipient_connection_id = Column(Integer, ForeignKey('linkedin_connections.id'))
    response = Column(Integer, default=0)

    # -- ORM --------------------------
    template = relationship("LinkedInMessageTemplate", uselist=False, back_populates="instances")
    recipient = relationship("LinkedInConnection", uselist=False, back_populates="messages")
    account = relationship("LinkedInAccount", uselist=False, back_populates="messages")

class ResponseMeanings(Base):
    """Meaning of message responses"""

    __tablename__ = "response_meanings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    meaning = Column(String, unique=True)

if __name__ == '__main__':
    clients = session.query(Client).all()
    for c in clients:
        print(c.linkedin_account.username)
        for connection in c.linkedin_account.connections:
            print("\t" + connection.name)