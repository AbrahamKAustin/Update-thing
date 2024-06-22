from pydantic import BaseModel

class CompanyAdd(BaseModel):
    ticker: str
    name: str
    last_sale: float
    market_cap: float
    sector: str
    industry: str
    cik: int
    exchange: str

class CompanyUpdate(BaseModel):
    ticker: str
    last_sale: float

    class Config:
        orm_mode = True