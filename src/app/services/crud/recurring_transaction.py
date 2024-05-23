from datetime import datetime, timedelta
from fastapi import HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.transaction import RecurringTransactionCreate, TransactionCreate
from app.services.crud.transaction import create_transaction
from app.sql_app.models.enumerate import IntervalType
from app.sql_app.models.models import  RecurringTransaction, Transaction, Card, User, Wallet
from uuid import UUID
import uuid
import pytz


async def create_recurring_transaction(db: AsyncSession, transaction_data: RecurringTransactionCreate, sender_id: UUID) -> Transaction:
    """
    Create a new recurring transaction for the user. It will be executed at the specified interval.
        Parameters:
            db (AsyncSession): The database session.
            transaction_data (RecurringTransactionCreate): The recurring transaction data.
            sender_id (UUID): The ID of the sender.
        Returns:
            RecurringTransaction: The created recurring transaction object.
    """
    sender_result = await db.execute(select(User).where(User.id == sender_id))
    sender = sender_result.scalars().first()
    if not sender:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="Sender not found.")
    if sender.is_blocked:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, 
                            detail="Sender is blocked.")
    
    sender_wallet_result = await db.execute(select(Wallet).where(Wallet.user_id == sender_id))
    sender_wallet = sender_wallet_result.scalars().first()
    if not sender_wallet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Sender's wallet not found.")
    if sender_wallet.balance < transaction_data.amount:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Insufficient funds.")

    card_result = await db.execute(select(Card).where(Card.id == transaction_data.card_id, Card.user_id == sender_id))
    card = card_result.scalars().first()
    if not card:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found.")

    recipient_wallet_result = await db.execute(select(Wallet).where(Wallet.user_id == transaction_data.recipient_id))
    recipient_wallet = recipient_wallet_result.scalars().first()
    if not recipient_wallet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Recipient's wallet not found.")
    
    new_transaction = RecurringTransaction(id=uuid.uuid4(),
                                           user_id=sender_id,
                                           card_id=transaction_data.card_id,
                                           recipient_id=transaction_data.recipient_id,
                                           category_id=transaction_data.category_id,
                                           amount=transaction_data.amount,
                                           interval=transaction_data.interval,
                                           interval_type=transaction_data.interval_type,
                                           next_execution_date=transaction_data.next_execution_date) 
    db.add(new_transaction)
    await db.commit()
    await db.refresh(new_transaction)
    return new_transaction


async def process_recurring_transactions(db: AsyncSession):
    """
    Process any recurring transactions that are due for payment.
        Parameters:
            db (AsyncSession): The database session.
        """
    current_time = datetime.now(pytz.utc)
    result = await db.execute(select(RecurringTransaction).where(and_(RecurringTransaction.next_execution_date <= current_time)))
    due_recurring_transactions = result.scalars().all()
    for recurring_transaction in due_recurring_transactions:
        transaction_data = TransactionCreate(amount=recurring_transaction.amount,
                                             timestamp=datetime.now(pytz.utc),
                                             card_id=recurring_transaction.card_id,
                                             recipient_id=recurring_transaction.recipient_id,
                                             category_id=recurring_transaction.category_id,)
        try:
            await create_transaction(db, transaction_data, recurring_transaction.user_id)
            if recurring_transaction.interval_type == IntervalType.DAILY:
                recurring_transaction.next_execution_date += timedelta(days=1)
            elif recurring_transaction.interval_type == IntervalType.WEEKLY:
                recurring_transaction.next_execution_date += timedelta(weeks=1)
            elif recurring_transaction.interval_type == IntervalType.MONTHLY:
                next_month = recurring_transaction.next_execution_date.month % 12 + 1
                next_year = recurring_transaction.next_execution_date.year + \
                            (recurring_transaction.next_execution_date.month // 12)
                recurring_transaction.next_execution_date = recurring_transaction.next_execution_date.replace(month=next_month, year=next_year)
            db.add(recurring_transaction)
            await db.commit()
        except Exception as e:
            await db.rollback()
            raise e