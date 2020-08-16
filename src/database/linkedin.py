import datetime
from datetime import date, datetime, timedelta
from Cryptodome.Cipher import AES
from sqlalchemy import Column, String, Boolean, Date, Time, DateTime, Integer, ForeignKey, LargeBinary
from sqlalchemy.orm import relationship
from database.credentials import AES_key
from database.general import Base, Session


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
    client = relationship("Client", uselist=False, back_populates="linkedin_account")
    connections = relationship("LinkedInConnection", uselist=True, back_populates="account")
    messages = relationship("LinkedInMessage", uselist=True, back_populates="account")
    message_templates = relationship("LinkedInMessageTemplate", uselist=True, back_populates="account")
    daily_activity = relationship("LinkedInAccountDailyActivity", uselist=True, back_populates="account")

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

    def setActivityLimitForToday(self, newLimit: int):
        """Change the daily account limit for this account for today only"""
        activityToday = LinkedInAccountDailyActivity.getToday(self.id)
        activityToday.activity_limit = newLimit
        Session.commit()

    def getDailyActivityLimit(self):
        """Get the linkedin account's daily activity limit"""
        return LinkedInAccountDailyActivity.getToday(self.id).activity_limit

    def dailyActivityLimitReached(self):
        """Determine if this account has reached its daily activity limit."""
        activityToday = LinkedInAccountDailyActivity.getToday(self.id)
        return activityToday.message_count + activityToday.connection_request_count >= activityToday.activity_limit

class LinkedInAccountDailyActivity(Base):
    """Keeps track of a single LinkedIn account's daily activity."""

    __tablename__ = "linkedin_accounts_daily_activity"

    DEFAULT_ACTIVITY_LIMIT = 100
    MAX_ACTIVITY_LIMIT = 200
    MINIMUM_ACTIVITY_INERVAL = 1 # seconds

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey('linkedin_accounts.id'))
    date = Column(Date)
    message_count = Column(Integer, default=0)
    connection_request_count = Column(Integer, default=0)
    activity_limit = Column(Integer, default=DEFAULT_ACTIVITY_LIMIT)
    last_activity = Column(DateTime, default=datetime.utcnow)

    # -- ORM --------------------------
    account = relationship("LinkedInAccount", uselist=False, back_populates="daily_activity")

    @staticmethod
    def getToday(account_id: int) -> 'LinkedInAccountDailyActivity':
        """
        Gets either the current day's activity record for any linkedin account.
        If it exists already, just return the record that exists.
        If not, create and return a new record with the limit automatically increased.
        """
        account = Session.query(LinkedInAccount).filter(
            LinkedInAccount.id == account_id
        ).one_or_none()

        assert account

        todaysActivity = Session.query(LinkedInAccountDailyActivity).filter(
            LinkedInAccountDailyActivity.account == account,
            LinkedInAccountDailyActivity.date == date.today()
        ).one_or_none()

        if todaysActivity:
            return todaysActivity

        lastDaysActivity = Session.query(LinkedInAccountDailyActivity).filter(
            LinkedInAccountDailyActivity.account == account,
            LinkedInAccountDailyActivity.date < date.today()
        ).order_by(
            LinkedInAccountDailyActivity.date
        ).first()

        if lastDaysActivity:
            newLimit = min(lastDaysActivity.activity_limit + 25, LinkedInAccountDailyActivity.MAX_ACTIVITY_LIMIT)
        else:
            newLimit = LinkedInAccountDailyActivity.DEFAULT_ACTIVITY_LIMIT

        newActivity = LinkedInAccountDailyActivity(account=account, date=date.today(), activity_limit=newLimit, message_count=0, connection_request_count=0)
        Session.add(newActivity)
        Session.commit()
        return newActivity


class LinkedInConnection(Base):
    """LinkedIn Connections belonging to our clients (connections mutual to multiple clients will be duplicated)"""

    __tablename__ = "linkedin_connections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey('linkedin_accounts.id'))
    name = Column(String)
    email = Column(String, default='')
    url = Column(String, default="")
    location = Column(String, default="")
    position = Column(String, default="")
    date_added = Column(DateTime, default=None)

    # -- ORM --------------------------
    account = relationship("LinkedInAccount", uselist=False, back_populates="connections")
    messages = relationship("LinkedInMessage", uselist=True, back_populates="recipient")


class LinkedInMessageTemplate(Base):
    """Message templates for LinkedIn that will be blasted out to our connections"""

    __tablename__ = "linkedin_message_templates"

    invalidPlaceholder = "INVALID-PLACEHOLDER"
    defaultCRC = -1

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey('linkedin_accounts.id'))
    name = Column(String, nullable=False)
    message_template = Column(String, unique=True)
    crc = Column(Integer, default=defaultCRC)
    date_created = Column(DateTime, default=datetime.utcnow)
    deleted = Column(Boolean, default=False)

    # -- ORM --------------------------
    account = relationship("LinkedInAccount", uselist=False, back_populates="message_templates")
    instances = relationship("LinkedInMessage", uselist=True, back_populates="template")

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
            "{FIRST_NAME}": lambda c: c.name.strip().split()[0],
            "{LAST_NAME}":  lambda c: c.name.strip().split()[-1],
            "{FULL_NAME}":  lambda c: c.name.strip(),
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
        """Determines if a template was filled properly"""
        text = self.fill(connection)
        return not self.invalidPlaceholder in text


class LinkedInMessage(Base):
    """Instances of the Message templates that we actually sent to connections."""

    __tablename__ = "linkedin_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey('linkedin_accounts.id'))
    template_id = Column(Integer, ForeignKey('linkedin_message_templates.id'))
    recipient_connection_id = Column(Integer, ForeignKey('linkedin_connections.id'))
    time_sent = Column(DateTime, default=datetime.utcnow)
    response = Column(Integer, default=0)

    # -- ORM --------------------------
    template = relationship("LinkedInMessageTemplate", uselist=False, back_populates="instances")
    recipient = relationship("LinkedInConnection", uselist=False, back_populates="messages")
    account = relationship("LinkedInAccount", uselist=False, back_populates="messages")

    def text(self):
        """Replaces the placeholders in the template with connection info and returns a linkedin message"""
        return self.template.fill(self.recipient)

    def isValid(self):
        """Determines if a template was filled properly"""
        return self.template.isValid(self.recipient)

    def recordAsDelivered(self):
        """Increments the message count for the corresponding account"""
        todaysActivity = LinkedInAccountDailyActivity.getToday(self.account.id)
        todaysActivity.message_count += 1
        todaysActivity.last_activity = datetime.now()
        Session.flush()


class ResponseMeanings(Base):
    """Meaning of message responses"""

    __tablename__ = "response_meanings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    meaning = Column(String, unique=True)
