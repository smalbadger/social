from sqlalchemy import create_engine
from sqlalchemy import Column, String, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from database.credentials import username, password, host, port
from database.linkedin import Client, LinkedInMessage, LinkedInAccount, LinkedInConnection, LinkedInMessageTemplate
from database.linkedin import session as newSession

engine = create_engine(f'mysql+pymysql://{username}:{password}@{host}:{port}/linkedin', pool_recycle=3600)
session = sessionmaker(bind=engine)()

Base = declarative_base()

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

def migrateOldDatabase():
    """
    DO NOT RUN THIS FUNCTION

    This function takes all of the data from Tony's prototype database and ports it to the new database.

    This function is very bad code. It assumes that only one templated message has been sent and only by Steve Sims.
    :return:
    """

    return  # in case someone runs this function

    contacts = session.query(Contacts).all()
    messages = session.query(Messages).all()

    message_templates_dict = {}
    msg_template = None
    for m in messages:
        if "Hi [First Name]" in m.MSG:
            msg_template = LinkedInMessageTemplate(message_template=m.MSG, crc=m.MSG_CRC, date_created=m.Date_Created)
            newSession.add(msg_template)
            message_templates_dict[m.MSG_CRC] = msg_template

    client_dict = {}
    account_dict = {}
    connection_dict = {}
    steve = None

    for c in contacts:

        if len(c.Account.split()) > 1:

            if c.Account not in client_dict:
                client = Client(name=c.Account, email="", phone="", tester=False)
                account = LinkedInAccount(username=c.Account, email="", password="")
                client.linkedin_account = account
                client_dict[c.Account] = client
                account_dict[c.Account] = account
                newSession.add(client)
                newSession.add(account)

                if c.Account == "Steve Sims":
                    account.message_templates += [msg for msg in message_templates_dict.values() if "Hi [First Name]" in msg.message_template]
                    steve = account

            if c.Full_Name:
                connection = LinkedInConnection(name=c.Full_Name, account=account_dict[c.Account], url="", location="", position="")
                newSession.add(connection)
                connection_dict[f"{c.Account} -> {c.Full_Name}"] = connection

                if c.Account == "Steve Sims":
                    msg = LinkedInMessage(template=msg_template, recipient=connection, account=steve)
                    newSession.add(msg)

    newSession.commit()