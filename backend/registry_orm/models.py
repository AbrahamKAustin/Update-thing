from sqlalchemy import Column, Integer, String, Float
from .database import Base

class Company(Base):
    __tablename__ = "company_reference"
    ticker = Column(String, primary_key=True, index=True, nullable=False)
    name = Column(String)
    market_cap = Column(Float)
    sector = Column(String)
    industry = Column(String)
    cik = Column(String, index=True)
    exchange = Column(String)