from sqlalchemy import Column, Integer, String, Float
from .database import Base

class Company(Base):
    __tablename__ = "company_identification"
    ticker = Column(String, primary_key=True, index=True)
    name = Column(String)
    last_sale = Column(Float)
    market_cap = Column(Float)
    sector = Column(String)
    industry = Column(String)
    cik = Column(Integer, index=True)
    exchange = Column(String)
