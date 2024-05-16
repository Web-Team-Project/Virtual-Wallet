from fastapi import HTTPException, status
from app.schemas.card import CardCreate
from app.sql_app.models.models import Card
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

async def create_card(db: AsyncSession, card: CardCreate, user_id: int):
    db_card = Card(number=card.number, 
                   card_holder=card.card_holder, 
                   exp_date=card.exp_date, 
                   cvv=card.cvv, 
                   design=card.design, 
                   user_id=user_id)
    db.add(db_card)
    await db.commit()
    await db.refresh(db_card)
    return db_card


async def read_card(db: AsyncSession, card_id: int):
    stmt = select(Card).where(Card.id == card_id)
    result = await db.execute(stmt)
    db_card = result.scalars().first()
    if db_card is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="Card not found.")
    return db_card


async def update_card(db: AsyncSession, card_id: int, card: CardCreate, user_id: int):
    stmt = select(Card).where(Card.id == card_id, Card.user_id == user_id)
    result = await db.execute(stmt)
    db_card = result.scalars().first()
    if not db_card:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="Card not found.")
    db_card.number = card.number
    db_card.card_holder = card.card_holder
    db_card.exp_date = card.exp_date
    db_card.cvv = card.cvv
    db_card.design = card.design
    await db.commit()
    await db.refresh(db_card)
    return db_card


async def delete_card(db: AsyncSession, card_id: int, user_id: int):
    stmt = select(Card).where(Card.id == card_id, Card.user_id == user_id)
    result = await db.execute(stmt)
    db_card = result.scalars().first()
    if db_card is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="Card not found.")
    db.delete(db_card)
    await db.commit()
    return {"message": "Card deleted successfully."}