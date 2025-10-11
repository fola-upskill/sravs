"""
Mock Payment Gateway Service for Student Records System
Handles payment processing for transcript requests
"""

import logging
import uuid
import random
from typing import Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from enum import Enum

logger = logging.getLogger(__name__)

class PaymentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    REFUNDED = "refunded"

class PaymentMethod(str, Enum):
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    PAYPAL = "paypal"
    BANK_TRANSFER = "bank_transfer"

class MockPaymentGateway:
    """Mock payment gateway for testing purposes"""
    
    def __init__(self):
        self.transactions = {}
        
        # Configuration
        self.transcript_fee = 25.00  # Fixed fee in USD
        self.processing_fee = 2.50   # Processing fee
        self.currency = "USD"
        
        # Simulate different success rates for testing
        self.success_rate = 0.95  # 95% success rate
        
    def calculate_total_amount(self, transcript_count: int = 1) -> Dict[str, Any]:
        """Calculate total payment amount"""
        base_amount = self.transcript_fee * transcript_count
        processing_fee = self.processing_fee
        total_amount = base_amount + processing_fee
        
        return {
            "base_amount": base_amount,
            "processing_fee": processing_fee,
            "total_amount": total_amount,
            "currency": self.currency,
            "transcript_count": transcript_count
        }
    
    async def create_payment_intent(
        self, 
        student_id: str, 
        student_email: str,
        transcript_count: int = 1,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a payment intent for transcript request"""
        
        payment_id = str(uuid.uuid4())
        amount_details = self.calculate_total_amount(transcript_count)
        
        payment_intent = {
            "payment_id": payment_id,
            "student_id": student_id,
            "student_email": student_email,
            "status": PaymentStatus.PENDING,
            "amount_details": amount_details,
            "created_at": datetime.now(timezone.utc),
            "expires_at": datetime.now(timezone.utc) + timedelta(minutes=30),  # 30 min expiry
            "metadata": metadata or {},
            "client_secret": f"pi_{payment_id}_secret_mock"
        }
        
        self.transactions[payment_id] = payment_intent
        
        logger.info(f"Created payment intent {payment_id} for student {student_id}")
        
        return {
            "success": True,
            "payment_id": payment_id,
            "client_secret": payment_intent["client_secret"],
            "amount_details": amount_details,
            "expires_at": payment_intent["expires_at"].isoformat()
        }
    
    async def process_payment(
        self,
        payment_id: str,
        payment_method: PaymentMethod,
        payment_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process the payment (mock implementation)"""
        
        if payment_id not in self.transactions:
            return {
                "success": False,
                "error": "Payment intent not found",
                "error_code": "payment_not_found"
            }
        
        payment = self.transactions[payment_id]
        
        # Check if payment is expired
        if datetime.now(timezone.utc) > payment["expires_at"]:
            payment["status"] = PaymentStatus.FAILED
            return {
                "success": False,
                "error": "Payment intent expired",
                "error_code": "payment_expired"
            }
        
        # Check if already processed
        if payment["status"] != PaymentStatus.PENDING:
            return {
                "success": False,
                "error": f"Payment already {payment['status']}",
                "error_code": "payment_already_processed"
            }
        
        # Update payment status
        payment["status"] = PaymentStatus.PROCESSING
        payment["payment_method"] = payment_method
        payment["payment_details"] = {
            "card_last_four": payment_details.get("card_number", "1234")[-4:] if payment_method in ["credit_card", "debit_card"] else None,
            "card_brand": payment_details.get("card_brand", "visa"),
            "processed_at": datetime.now(timezone.utc)
        }
        
        # Simulate processing delay
        import asyncio
        await asyncio.sleep(2)
        
        # Simulate success/failure based on success rate
        is_success = random.random() < self.success_rate
        
        if is_success:
            payment["status"] = PaymentStatus.SUCCESS
            payment["transaction_id"] = f"txn_{uuid.uuid4().hex[:16]}"
            payment["processed_at"] = datetime.now(timezone.utc)
            
            logger.info(f"Payment {payment_id} processed successfully")
            
            return {
                "success": True,
                "payment_id": payment_id,
                "transaction_id": payment["transaction_id"],
                "status": PaymentStatus.SUCCESS,
                "amount_paid": payment["amount_details"]["total_amount"],
                "currency": payment["amount_details"]["currency"],
                "processed_at": payment["processed_at"].isoformat()
            }
        else:
            # Simulate failure reasons
            failure_reasons = [
                {"error": "Card declined", "error_code": "card_declined"},
                {"error": "Insufficient funds", "error_code": "insufficient_funds"},
                {"error": "Invalid card details", "error_code": "invalid_card"},
                {"error": "Processing error", "error_code": "processing_error"}
            ]
            
            failure = random.choice(failure_reasons)
            payment["status"] = PaymentStatus.FAILED
            payment["failure_reason"] = failure["error"]
            payment["failure_code"] = failure["error_code"]
            
            logger.warning(f"Payment {payment_id} failed: {failure['error']}")
            
            return {
                "success": False,
                "payment_id": payment_id,
                "error": failure["error"],
                "error_code": failure["error_code"],
                "status": PaymentStatus.FAILED
            }
    
    async def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """Get payment status and details"""
        
        if payment_id not in self.transactions:
            return {
                "success": False,
                "error": "Payment not found"
            }
        
        payment = self.transactions[payment_id]
        
        return {
            "success": True,
            "payment_id": payment_id,
            "status": payment["status"],
            "amount_details": payment["amount_details"],
            "created_at": payment["created_at"].isoformat(),
            "processed_at": payment.get("processed_at", {}).isoformat() if payment.get("processed_at") else None,
            "transaction_id": payment.get("transaction_id"),
            "payment_method": payment.get("payment_method"),
            "failure_reason": payment.get("failure_reason")
        }
    
    async def refund_payment(self, payment_id: str, reason: str = "Transcript request cancelled") -> Dict[str, Any]:
        """Process a refund for a payment"""
        
        if payment_id not in self.transactions:
            return {
                "success": False,
                "error": "Payment not found"
            }
        
        payment = self.transactions[payment_id]
        
        if payment["status"] != PaymentStatus.SUCCESS:
            return {
                "success": False,
                "error": "Can only refund successful payments"
            }
        
        # Process refund (mock)
        payment["status"] = PaymentStatus.REFUNDED
        payment["refunded_at"] = datetime.now(timezone.utc)
        payment["refund_reason"] = reason
        payment["refund_id"] = f"rf_{uuid.uuid4().hex[:16]}"
        
        logger.info(f"Payment {payment_id} refunded: {reason}")
        
        return {
            "success": True,
            "payment_id": payment_id,
            "refund_id": payment["refund_id"],
            "refund_amount": payment["amount_details"]["total_amount"],
            "refunded_at": payment["refunded_at"].isoformat(),
            "reason": reason
        }
    
    def get_payment_summary(self) -> Dict[str, Any]:
        """Get summary of all payments for analytics"""
        
        total_payments = len(self.transactions)
        successful_payments = len([p for p in self.transactions.values() if p["status"] == PaymentStatus.SUCCESS])
        failed_payments = len([p for p in self.transactions.values() if p["status"] == PaymentStatus.FAILED])
        pending_payments = len([p for p in self.transactions.values() if p["status"] == PaymentStatus.PENDING])
        
        total_revenue = sum([
            p["amount_details"]["total_amount"] 
            for p in self.transactions.values() 
            if p["status"] == PaymentStatus.SUCCESS
        ])
        
        return {
            "total_payments": total_payments,
            "successful_payments": successful_payments,
            "failed_payments": failed_payments,
            "pending_payments": pending_payments,
            "success_rate": (successful_payments / total_payments * 100) if total_payments > 0 else 0,
            "total_revenue": total_revenue,
            "currency": self.currency,
            "average_transaction": total_revenue / successful_payments if successful_payments > 0 else 0
        }

# Global payment service instance
payment_gateway = MockPaymentGateway()