import datetime
from Cryptodome.Cipher import AES
from sqlalchemy import create_engine
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

from database.credentials import username, password, host, port, AES_key

engine = create_engine(f'mysql+pymysql://{username}:{password}@{host}:{port}/social', pool_recycle=3600, connect_args={'connect_timeout': 10})
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
    profile_name = Column(String)
    password = Column(LargeBinary)
    flagged_as_bot_date = Column(DateTime, default=None)
    flagged_as_bot = Column(Integer, default=0)
    tester = Column(Boolean, default=False)

    # -- ORM --------------------------
    client = relationship("Client", back_populates="linkedin_account")
    connections = relationship("LinkedInConnection", back_populates="account")
    messages = relationship("LinkedInMessage", back_populates="account")
    message_templates = relationship("LinkedInMessageTemplate", back_populates="account")

    def getPassword(self):
        """Get the decrypted password"""
        nonce = self.password[0:16]
        ciphertext = self.password[16:]
        cipher = AES.new(AES_key, AES.MODE_EAX, nonce=nonce)
        plaintext = cipher.decrypt(ciphertext).decode("utf-8")
        return plaintext

    def setPassword(self, password):
        """Encrypt the password and store it"""
        cipher = AES.new(AES_key, AES.MODE_EAX)
        nonce = cipher.nonce
        ciphertext, tag = cipher.encrypt_and_digest(password.encode("utf-8"))
        self.password = nonce + ciphertext

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
    account = relationship("LinkedInAccount", back_populates="connections")
    messages = relationship("LinkedInMessage", back_populates="recipient")

class LinkedInMessageTemplate(Base):
    """Message templates for LinkedIn that will be blasted out to our connections"""

    __tablename__ = "linkedin_message_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey('linkedin_accounts.id'))
    message_template = Column(String, unique=True)
    crc = Column(Integer)
    date_created = Column(DateTime, default=datetime.datetime.utcnow)

    # -- ORM --------------------------
    account = relationship("LinkedInAccount", back_populates="message_templates")
    instances = relationship("LinkedInMessage", back_populates="template")

class LinkedInMessage(Base):
    """Instances of the Message templates that we actually sent to connections."""

    __tablename__ = "linkedin_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey('linkedin_accounts.id'))
    template_id = Column(Integer, ForeignKey('linkedin_message_templates.id'))
    recipient_connection_id = Column(Integer, ForeignKey('linkedin_connections.id'))
    response = Column(Integer, default=0)

    # -- ORM --------------------------
    template = relationship("LinkedInMessageTemplate", back_populates="instances")
    recipient = relationship("LinkedInConnection", back_populates="messages")
    account = relationship("LinkedInAccount", back_populates="messages")

class ResponseMeanings(Base):
    """Meaning of message responses"""

    __tablename__ = "response_meanings"

    # -- ORM --------------------------
    id = Column(Integer, primary_key=True, autoincrement=True)
    meaning = Column(String, unique=True)
