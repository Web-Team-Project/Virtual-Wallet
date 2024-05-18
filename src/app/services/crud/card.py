from fastapi import HTTPException, status
from app.schemas.card import CardCreate
from app.sql_app.models.models import User, Card
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID


async def create_card(db: AsyncSession, card: CardCreate, user_id: UUID):
    db_card = Card(number=card.number, 
                   card_holder=card.card_holder, 
                   exp_date=card.exp_date, 
                   cvv=card.cvv, 
                   design=card.design, 
                   user_id=card.user_id)
    db.add(db_card)
    await db.commit()
    await db.refresh(db_card)
    return db_card


async def read_card(db: AsyncSession, card_id: UUID):
    result = await db.execute(select(Card).where(Card.id == card_id))
    db_card = result.scalars().first()
    if db_card is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="Card not found.")
    return db_card


async def update_card(db: AsyncSession, card_id: UUID, card: CardCreate, current_user: User):
    result = await db.execute(select(Card).where(Card.id == card_id))
    db_card = result.scalars().first()
    if not db_card:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="Card not found.")
    if db_card.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, 
                            detail="Not authorized to update this card.")
    db_card.number = card.number
    db_card.card_holder = card.card_holder
    db_card.exp_date = card.exp_date
    db_card.cvv = card.cvv
    db_card.design = card.design
    await db.commit()
    await db.refresh(db_card)
    return db_card


async def delete_card(db: AsyncSession, card_id: UUID, user_id: UUID):
    result = await db.execute(select(Card).where(and_(Card.id == card_id, Card.user_id == user_id)))
    db_card = result.scalars().first()
    if db_card is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="Card not found.")
    db.delete(db_card)
    await db.commit()
    return {"message": "Card deleted successfully."}