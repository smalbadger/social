from database.credentials import username, password, host, port

from sqlalchemy import Column, String, Boolean, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import create_engine

engine = create_engine(f'mysql+pymysql://{username}:{password}@{host}:{port}/social',
                       pool_recycle=3600,
                       connect_args={'connect_timeout': 10})
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
