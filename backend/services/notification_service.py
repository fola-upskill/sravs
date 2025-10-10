"""
Notification service for real-time updates and automated verification alerts
Handles WebSocket connections, email notifications, and dashboard alerts
"""

import asyncio
import json
import logging
from typing import Dict, List, Set, Optional, Any
from datetime import datetime, timezone
from fastapi import WebSocket
from enum import Enum
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

logger = logging.getLogger(__name__)

class NotificationType(str, Enum):
    NEW_REQUEST = "new_request"
    VERIFICATION_COMPLETE = "verification_complete" 
    REQUEST_APPROVED = "request_approved"
    REQUEST_REJECTED = "request_rejected"
    BLOCKCHAIN_CONFIRMED = "blockchain_confirmed"
    SYSTEM_ALERT = "system_alert"

class NotificationPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class NotificationService:
    """Service for managing real-time notifications and alerts"""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {
            "student": set(),
            "issuer": set(), 
            "verifier": set(),
            "admin": set()
        }
        self.notification_queue: List[Dict[str, Any]] = []
        
        # Email configuration
        self.smtp_server = os.getenv('SMTP_SERVER', 'localhost')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.from_email = os.getenv('FROM_EMAIL', 'noreply@studentrecords.edu')
        
    async def connect_websocket(self, websocket: WebSocket, user_role: str, user_id: str):
        """Connect a WebSocket for real-time notifications"""
        await websocket.accept()
        
        if user_role not in self.active_connections:
            self.active_connections[user_role] = set()
            
        self.active_connections[user_role].add(websocket)
        logger.info(f"WebSocket connected for {user_role} user {user_id}")
        
        try:
            # Send welcome message
            await self.send_notification_to_websocket(
                websocket,
                NotificationType.SYSTEM_ALERT,
                "Connected to real-time notifications",
                {"status": "connected", "timestamp": datetime.now(timezone.utc).isoformat()}
            )
            
            # Keep connection alive
            while True:
                await websocket.receive_text()
                
        except Exception as e:
            logger.info(f"WebSocket disconnected for {user_role} user {user_id}: {e}")
        finally:
            self.active_connections[user_role].discard(websocket)
    
    async def send_notification_to_websocket(
        self, 
        websocket: WebSocket, 
        notification_type: NotificationType,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ):
        """Send notification to a specific WebSocket"""
        try:
            notification = {
                "type": notification_type.value,
                "message": message,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": data or {}
            }
            await websocket.send_text(json.dumps(notification))
        except Exception as e:
            logger.error(f"Failed to send WebSocket notification: {e}")
    
    async def broadcast_to_role(
        self, 
        user_role: str,
        notification_type: NotificationType,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        priority: NotificationPriority = NotificationPriority.MEDIUM
    ):
        """Broadcast notification to all connected users of a specific role"""
        if user_role not in self.active_connections:
            return
        
        # Add notification to queue for persistence
        self.notification_queue.append({
            "role": user_role,
            "type": notification_type.value,
            "message": message,
            "data": data or {},
            "priority": priority.value,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        # Send to active connections
        disconnected_sockets = set()
        for websocket in self.active_connections[user_role]:
            try:
                await self.send_notification_to_websocket(
                    websocket, notification_type, message, data
                )
            except Exception as e:
                logger.warning(f"Failed to send to WebSocket: {e}")
                disconnected_sockets.add(websocket)
        
        # Clean up disconnected sockets
        for socket in disconnected_sockets:
            self.active_connections[user_role].discard(socket)
    
    async def notify_new_transcript_request(
        self, 
        request_data: Dict[str, Any],
        issuer_university: str
    ):
        """Notify issuers about new transcript requests"""
        message = f"New transcript request from {request_data.get('student_name')} for {issuer_university}"
        
        await self.broadcast_to_role(
            "issuer",
            NotificationType.NEW_REQUEST,
            message,
            {
                "request_id": request_data.get("id"),
                "student_name": request_data.get("student_name"),
                "student_email": request_data.get("student_email"),
                "university_from": request_data.get("university_from"),
                "university_to": request_data.get("university_to"),
                "document_type": request_data.get("document_type"),
                "created_at": request_data.get("created_at"),
                "action_required": True
            },
            NotificationPriority.HIGH
        )
    
    async def notify_verification_complete(
        self,
        request_data: Dict[str, Any],
        blockchain_data: Dict[str, Any]
    ):
        """Notify about completed blockchain verification"""
        student_message = f"Your {request_data.get('document_type')} has been verified on the blockchain"
        verifier_message = f"Verified {request_data.get('document_type')} from {request_data.get('university_from')} is ready"
        
        # Notify student
        await self.broadcast_to_role(
            "student",
            NotificationType.BLOCKCHAIN_CONFIRMED,
            student_message,
            {
                "request_id": request_data.get("id"),
                "transaction_hash": blockchain_data.get("transaction_hash"),
                "block_number": blockchain_data.get("block_number"),
                "document_hash": blockchain_data.get("document_hash"),
                "verified": True
            },
            NotificationPriority.MEDIUM
        )
        
        # Notify verifier
        await self.broadcast_to_role(
            "verifier", 
            NotificationType.VERIFICATION_COMPLETE,
            verifier_message,
            {
                "request_id": request_data.get("id"),
                "student_name": request_data.get("student_name"),
                "university_from": request_data.get("university_from"),
                "blockchain_verified": True,
                "verification_url": f"/verify/{blockchain_data.get('document_hash')}"
            },
            NotificationPriority.MEDIUM
        )
    
    async def notify_issuer_action(
        self,
        action: str,  # "approved" or "rejected"
        request_data: Dict[str, Any],
        validation_data: Dict[str, Any]
    ):
        """Notify about issuer actions on transcript requests"""
        status = "approved" if action == "approved" else "rejected"
        message = f"Your transcript request has been {status}"
        
        notification_type = (
            NotificationType.REQUEST_APPROVED if action == "approved" 
            else NotificationType.REQUEST_REJECTED
        )
        
        # Notify student
        await self.broadcast_to_role(
            "student",
            notification_type,
            message,
            {
                "request_id": request_data.get("id"),
                "issuer_name": validation_data.get("issuer_name"),
                "validation_notes": validation_data.get("validation_notes"),
                "university_from": request_data.get("university_from"),
                "status": status,
                "next_steps": "Your verified document will be sent to the receiving institution" if action == "approved" else "Please contact your issuing institution for more information"
            },
            NotificationPriority.HIGH
        )
    
    async def send_email_notification(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None
    ):
        """Send email notification"""
        if not self.smtp_username or not self.smtp_password:
            logger.warning("Email credentials not configured - skipping email notification")
            return False
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            # Add text version
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)
            
            # Add HTML version if provided
            if html_body:
                html_part = MIMEText(html_body, 'html')
                msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    async def send_verification_email(
        self,
        to_email: str,
        student_name: str,
        document_type: str,
        verification_url: str,
        blockchain_hash: str
    ):
        """Send verification completion email"""
        subject = f"Your {document_type} has been verified"
        
        body = f"""
Dear {student_name},

Your {document_type} has been successfully verified and recorded on the blockchain.

Verification Details:
- Document Type: {document_type}
- Verification Hash: {blockchain_hash}
- Verification URL: {verification_url}

This verification provides cryptographic proof of authenticity and cannot be tampered with.

Best regards,
Student Records Verification System
        """.strip()
        
        html_body = f"""
<html>
<body>
    <h2>Verification Complete</h2>
    <p>Dear {student_name},</p>
    
    <p>Your <strong>{document_type}</strong> has been successfully verified and recorded on the blockchain.</p>
    
    <h3>Verification Details</h3>
    <ul>
        <li><strong>Document Type:</strong> {document_type}</li>
        <li><strong>Verification Hash:</strong> <code>{blockchain_hash}</code></li>
        <li><strong>Verification URL:</strong> <a href="{verification_url}">{verification_url}</a></li>
    </ul>
    
    <p>This verification provides cryptographic proof of authenticity and cannot be tampered with.</p>
    
    <p>Best regards,<br>Student Records Verification System</p>
</body>
</html>
        """.strip()
        
        return await self.send_email_notification(to_email, subject, body, html_body)
    
    def get_notification_stats(self) -> Dict[str, Any]:
        """Get notification system statistics"""
        active_count = sum(len(connections) for connections in self.active_connections.values())
        
        return {
            "active_connections": {
                role: len(connections) 
                for role, connections in self.active_connections.items()
            },
            "total_active": active_count,
            "queued_notifications": len(self.notification_queue),
            "recent_notifications": self.notification_queue[-10:]  # Last 10 notifications
        }
    
    def get_recent_notifications(self, role: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent notifications for a specific role"""
        return [
            notif for notif in self.notification_queue 
            if notif["role"] == role
        ][-limit:]

# Global notification service instance
notification_service = NotificationService()