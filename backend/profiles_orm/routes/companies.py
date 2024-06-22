from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas, database

router = APIRouter()

@router.post("/companies/", response_model=schemas.CompanyAdd)
def create_company(company: schemas.CompanyAdd, db: Session = Depends(database.get_db)):
    db_company = models.Company(
        ticker=company.ticker,
        name=company.name,
        last_sale=company.last_sale,
        market_cap=company.market_cap,
        sector=company.sector,
        industry=company.industry,
        cik=company.cik,
        exchange=company.exchange
    )
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    return db_company

@router.get("/get-company/{ticker}", response_model=schemas.CompanyAdd)
def get_company(ticker: str, db: Session = Depends(database.get_db)):
    db_company = db.query(models.Company).filter(models.Company.ticker == ticker).first()
    if db_company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return db_company

@router.delete("/delete-company/{ticker}", response_model=schemas.CompanyAdd)
def delete_company(ticker: str, db: Session = Depends(database.get_db)):
    db_company = db.query(models.Company).filter(models.Company.ticker == ticker).first()
    if db_company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    db.delete(db_company)
    db.commit()
    return db_company