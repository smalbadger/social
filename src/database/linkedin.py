"""
========================================================
Database Structure: Social
========================================================

Clients Table
-------------
    -> ID
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
from sqlalchemy import Column, String, Boolean, Integer, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
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

# class Client(Base):
#
#     __tablename__ = "Clients"
#
#     ID = Column(Integer, primary_key=True)
#     LinkedIn_Account = Column(Integer)
#
# class LinkedInAccount(Base):
#
#     __tablename__ = "LinkedIn Accounts"
#
#     ID = Column(Integer, primary_key=True)
#     Email = Column(String, unique=True)
#     Username = Column(String)
#     Password = Column(String)
#     Date_Created = Column(String)
#     Flagged_As_Bot = Column(Integer)
#
# class LinkedInConnection(Base):
#
#     __tablename__ = "LinkedIn Connections"
#
#     ID = Column(Integer, primary_key=True)
#     Account = Column()
#     Connecton_Name = Column(String)
#     Connection_URL = Column(String)
#
# class LinkedInMessageTemplate(Base):
#
#     __tablename__ = "LinkedIn Message Templates"





if __name__ == "__main__":

    contacts = session.query(Contacts).all()
    messages = session.query(Messages).all()

    for c in contacts:
        print(f"{c.Account} -> {c.Full_Name} -> {c.MSG_CRC}")

    for m in messages:
        print(m.MSG)

    print(f"# of contacts: {len(contacts)}")
    print(f"# of messages: {len(messages)}")
