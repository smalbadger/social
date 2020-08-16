import enum
from datetime import datetime
from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, DateTime, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, scoped_session
from sqlalchemy import create_engine

from database.credentials import username, password, host, port

engine = create_engine(f'mysql+pymysql://{username}:{password}@{host}:{port}/social',
                       pool_recycle=3600,
                       connect_args={'connect_timeout': 10})
Session = scoped_session(sessionmaker(bind=engine))

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


class Active(enum.Enum):
    true = True

class Version(Base):

    __tablename__ = "versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    semantic_id = Column(String)
    change_log = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    active = Column(Boolean, unique=True)
