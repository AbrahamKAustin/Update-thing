from pydantic import BaseModel

class CompanyAdd(BaseModel):
    ticker: str
    name: str
    market_cap: float
    sector: str
    industry: str
    cik: str
    exchange: str

    class Config:
        from_attributes = True

# If you need an update schema later, you can adjust it accordingly:
class CompanyUpdate(BaseModel):
    ticker: str
    # You can include any fields that need updating; for now, we'll omit last_sale.
    class Config:
        from_attributes = True