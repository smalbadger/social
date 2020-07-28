"""
========================================================
Database Structure: Social
========================================================

Clients Table
-------------
    -> ID
    -> Name
    -> Email
    -> Phone #
    -> linkedin account (From LinkedIn Accounts Table)
    ** Others to come

LinkedIn Accounts Table
-----------------------
    -> ID
    -> email (primary key)
    -> username
    -> password (AES encrypted)
    -> date flagged
    -> flagged as potential bot (0 for no, 1 for warning, 2 for banned)

LinkedIn Connections Table
--------------------------
    -> ID
    -> account (email from account table)
    -> connection name
    -> connection url

LinkedIn Message Templates
--------------------------
    -> ID
    -> account (email from account table)
    -> message template
    -> date created
    -> CRC

LinkedIn Messages (probably just the automated ones)
----------------------------------------------------
    -> ID
    -> account (email from account table)
    -> recipient
    -> message CRC
    -> meaning ID

Response Meaning
----------------
    -> ID
    -> meaning (STOP, INTERESTED, COMPLETED, etc.)





"""


from sqlalchemy import create_engine
from sqlalchemy import Column, String, Boolean, Integer, DateTime, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from pprint import pprint


engine = create_engine('mysql+pymysql://root:raspberry1!@k7aim.net:3306/linkedin', pool_recycle=3600)
session = sessionmaker(bind=engine)()
Base = declarative_base()

# --- Tony's Structure --------------------------------------------------------
class Contacts(Base):

    __tablename__ = "Contacts"

    ID = Column(Integer, primary_key=True)
    Account = Column(String)
    Full_Name = Column(String)
    First_Name = Column(String)
    List_Index = Column(Integer) # For keeping track of where you're at in the list of people
    Contact_Date = Column(DateTime)
    MSG_CRC = Column(Integer)

class Messages(Base):

    __tablename__ = "Messages"

    ID = Column(Integer, primary_key=True)
    Date_Created = Column(DateTime)
    MSG_CRC = Column(Integer)
    MSG = Column(String)

# --- Sam's Structure ---------------------------------------------------------

class Client(Base):

    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    email = Column(String, unique=True)
    phone = Column(String, unique=True)

    linkedin_account = relationship("LinkedInAccount", uselist=False, back_populates="client")

class LinkedInAccount(Base):

    __tablename__ = "linkedin_accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey('clients.id'))
    email = Column(String, unique=True)
    username = Column(String)
    password = Column(String)
    flagged_as_bot_date = Column(DateTime, default=None)
    flagged_as_bot = Column(Integer, default=0)

    client = relationship("Client", back_populates="linkedin_account")
    connections = relationship("LinkedInConnection", back_populates="account")
    messages = relationship("LinkedInMessage", back_populates="account")

class LinkedInConnection(Base):

    __tablename__ = "linkedin_connections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey('linkedin_accounts.id'))
    name = Column(String)
    url = Column(String)
    location = Column(String)
    position = Column(String)
    contact_date = Column(DateTime)

    account = relationship("LinkedInAccount", back_populates="connections")
    messages = relationship("LinkedInMessage", back_populates="connection")

class LinkedInMessageTemplate(Base):

    __tablename__ = "linkedin_message_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey('linkedin_accounts.id'))
    message_template = Column(String, unique=True)
    crc = Column(Integer)
    date_created = Column(DateTime)

    account = relationship("LinkedInAccount", back_populates="message_templates")
    instances = relationship("LinkedInMessage", back_populates="template")

class LinkedInMessage(Base):

    __tablename__ = "linkedin_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey('linkedin_accounts.id'))
    template_id = Column(Integer, ForeignKey('linkedin_message_templates.id'))
    recipient_connection_id = Column(Integer, ForeignKey('linkedin_connections.id'))
    message_crc = Column(Integer)
    response = Column(Integer)

    template = relationship("LinkedInMessageTemplate", back_populates="instances")
    recipient = relationship("LinkedInConnection", back_populates="messages")
    account = relationship("LinkedInAccount", back_populates="messages")

class ResponseMeanings(Base):

    __tablename__ = "response_meanings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    meaning = Column(String, unique=True)


def migrateOldDatabase():
    contacts = session.query(Contacts).all()
    messages = session.query(Messages).all()

    # messages_dict = {}
    # for m in messages:


    client_dict = {}
    account_dict = {}
    connection_dict = {}

    for c in contacts:
        if c.Account not in client_dict:
            client = Client(name=c.Full_Name)
            account = LinkedInAccount(username=c.Full_Name)
            client.linkedin_account = account
            account.client = client
            client_dict[c.Account] = client
            account_dict[c.Account] = account

        connection_dict[f"{c.Account} -> {c.Full_Name}"] = LinkedInConnection(account=account_dict[c.Account])

    print(connection_dict)
    print(account_dict)
    print(client_dict)


if __name__ == "__main__":

    migrateOldDatabase()
