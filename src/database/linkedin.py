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
        if not self.password:
            return ""

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

    invalidPlaceholder = "INVALID-PLACEHOLDER"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey('linkedin_accounts.id'))
    message_template = Column(String, unique=True)
    crc = Column(Integer)
    date_created = Column(DateTime, default=datetime.datetime.utcnow)

    # -- ORM --------------------------
    account = relationship("LinkedInAccount", back_populates="message_templates")
    instances = relationship("LinkedInMessage", back_populates="template")

    def createMessageTo(self, connection: LinkedInConnection):
        """Creates and returns a LinkedInMessage object"""
        return LinkedInMessage(account=self.account, template=self, recipient=connection)

    def fill(self, connection):
        """Replaces the placeholders in the template with connection info and returns a string"""
        templateText = self.message_template.encode('latin1').decode('unicode_escape')

        # all of the placeholders in the array (value), depend on the key attribute not being blank or null.
        connection_conditions = {
            "name": ["{FIRST_NAME}", "{LAST_NAME}", "{FULL_NAME}"],
            "location": ["{LOCATION}", "{CITY}", "{STATE}", "{COUNTRY}", "{ZIP_CODE}"]
        }

        # to replace the placeholders, call the following lambda functions.
        placeholders_functions = {
            "{FIRST_NAME}": lambda c: c.name.split()[0],
            "{LAST_NAME}":  lambda c: c.name.split()[-1],
            "{FULL_NAME}":  lambda c: c.name,
            "{LOCATION}":   lambda c: c.location,
            "{CITY}":       lambda c: self.invalidPlaceholder, # TODO: Extract city from location
            "{STATE}":      lambda c: self.invalidPlaceholder, # TODO: Extract state from location
            "{COUNTRY}":    lambda c: self.invalidPlaceholder, # TODO: Extract country from location
            "{ZIP_CODE}":   lambda c: self.invalidPlaceholder, # TODO: Extract zip code from location
        }

        for attr in connection_conditions:
            for placeholder in connection_conditions[attr]:
                if connection.__getattribute__(attr):
                    templateText = templateText.replace(placeholder, placeholders_functions[placeholder](connection))
                else:
                    templateText = templateText.replace(placeholder, self.invalidPlaceholder)

        return templateText

    def isValid(self, connection):
        text = self.fill(connection)
        return not self.invalidPlaceholder in text


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

    def text(self):
        """Replaces the placeholders in the template with connection info and returns a linkedin message"""
        return self.template.fill(self.recipient)

    def isValid(self):
        """Determines is a template was filled properly"""
        return self.template.isValid(self.recipient)


class ResponseMeanings(Base):
    """Meaning of message responses"""

    __tablename__ = "response_meanings"

    # -- ORM --------------------------
    id = Column(Integer, primary_key=True, autoincrement=True)
    meaning = Column(String, unique=True)
