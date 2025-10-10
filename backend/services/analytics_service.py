"""
Analytics service for dashboard insights and metrics
Provides comprehensive analytics for student records verification system
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
from enum import Enum

logger = logging.getLogger(__name__)

class MetricType(str, Enum):
    VERIFICATION_RATE = "verification_rate"
    PROCESSING_TIME = "processing_time"
    SUCCESS_RATE = "success_rate"
    VOLUME_TRENDS = "volume_trends"
    UNIVERSITY_STATS = "university_stats"
    BLOCKCHAIN_STATS = "blockchain_stats"

class AnalyticsService:
    """Service for generating analytics and insights"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    async def get_verification_overview(self, date_range: int = 30) -> Dict[str, Any]:
        """Get overall verification metrics for the dashboard"""
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=date_range)
        
        # Total requests in period
        total_requests = await self.db.transcript_requests.count_documents({
            "created_at": {"$gte": start_date, "$lte": end_date}
        })
        
        # Verified requests
        verified_requests = await self.db.transcript_requests.count_documents({
            "created_at": {"$gte": start_date, "$lte": end_date},
            "status": {"$in": ["validated", "received"]}
        })
        
        # Pending requests
        pending_requests = await self.db.transcript_requests.count_documents({
            "status": "pending"
        })
        
        # Blockchain verified requests
        blockchain_verified = await self.db.transcript_requests.count_documents({
            "content_hash": {"$exists": True, "$ne": ""},
            "created_at": {"$gte": start_date, "$lte": end_date}
        })
        
        # Calculate rates
        verification_rate = (verified_requests / total_requests * 100) if total_requests > 0 else 0
        blockchain_rate = (blockchain_verified / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "total_requests": total_requests,
            "verified_requests": verified_requests,
            "pending_requests": pending_requests,
            "blockchain_verified": blockchain_verified,
            "verification_rate": round(verification_rate, 2),
            "blockchain_rate": round(blockchain_rate, 2),
            "date_range": date_range,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
    
    async def get_daily_trends(self, days: int = 30) -> Dict[str, Any]:
        """Get daily verification trends"""
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        pipeline = [
            {
                "$match": {
                    "created_at": {"$gte": start_date, "$lte": end_date}
                }
            },
            {
                "$group": {
                    "_id": {
                        "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
                        "status": "$status"
                    },
                    "count": {"$sum": 1}
                }
            },
            {
                "$group": {
                    "_id": "$_id.date",
                    "statuses": {
                        "$push": {
                            "status": "$_id.status",
                            "count": "$count"
                        }
                    },
                    "total": {"$sum": "$count"}
                }
            },
            {"$sort": {"_id": 1}}
        ]
        
        results = await self.db.transcript_requests.aggregate(pipeline).to_list(None)
        
        # Process results into daily trends
        daily_data = []
        for day_data in results:
            status_counts = {item["status"]: item["count"] for item in day_data["statuses"]}
            daily_data.append({
                "date": day_data["_id"],
                "total": day_data["total"],
                "pending": status_counts.get("pending", 0),
                "validated": status_counts.get("validated", 0),
                "received": status_counts.get("received", 0),
                "rejected": status_counts.get("rejected", 0)
            })
        
        return {
            "trends": daily_data,
            "period": f"{days} days",
            "total_days": len(daily_data)
        }
    
    async def get_university_analytics(self) -> Dict[str, Any]:
        """Get analytics by university (issuers and verifiers)"""
        # Top issuing universities
        issuer_pipeline = [
            {"$group": {
                "_id": "$university_from",
                "total_requests": {"$sum": 1},
                "verified": {"$sum": {"$cond": [{"$in": ["$status", ["validated", "received"]]}, 1, 0]}},
                "pending": {"$sum": {"$cond": [{"$eq": ["$status", "pending"]}, 1, 0]}}
            }},
            {"$sort": {"total_requests": -1}},
            {"$limit": 10}
        ]
        
        top_issuers = await self.db.transcript_requests.aggregate(issuer_pipeline).to_list(None)
        
        # Top receiving universities
        verifier_pipeline = [
            {"$group": {
                "_id": "$university_to",
                "total_received": {"$sum": 1},
                "completed": {"$sum": {"$cond": [{"$eq": ["$status", "received"]}, 1, 0]}}
            }},
            {"$sort": {"total_received": -1}},
            {"$limit": 10}
        ]
        
        top_verifiers = await self.db.transcript_requests.aggregate(verifier_pipeline).to_list(None)
        
        return {
            "top_issuers": [
                {
                    "university": item["_id"],
                    "total_requests": item["total_requests"],
                    "verified": item["verified"],
                    "pending": item["pending"],
                    "verification_rate": round((item["verified"] / item["total_requests"] * 100), 2)
                }
                for item in top_issuers
            ],
            "top_verifiers": [
                {
                    "university": item["_id"],
                    "total_received": item["total_received"],
                    "completed": item["completed"],
                    "completion_rate": round((item["completed"] / item["total_received"] * 100), 2)
                }
                for item in top_verifiers
            ]
        }
    
    async def get_processing_time_analytics(self) -> Dict[str, Any]:
        """Get processing time analytics for verification workflow"""
        # Average time from request to validation
        request_to_validation_pipeline = [
            {
                "$lookup": {
                    "from": "issuer_validations",
                    "localField": "id",
                    "foreignField": "transcript_request_id",
                    "as": "validations"
                }
            },
            {"$unwind": "$validations"},
            {
                "$project": {
                    "processing_time_hours": {
                        "$divide": [
                            {"$subtract": ["$validations.validated_at", "$created_at"]},
                            1000 * 60 * 60  # Convert to hours
                        ]
                    }
                }
            },
            {
                "$group": {
                    "_id": None,
                    "avg_processing_time": {"$avg": "$processing_time_hours"},
                    "min_processing_time": {"$min": "$processing_time_hours"},
                    "max_processing_time": {"$max": "$processing_time_hours"},
                    "count": {"$sum": 1}
                }
            }
        ]
        
        processing_stats = await self.db.transcript_requests.aggregate(request_to_validation_pipeline).to_list(None)
        
        if processing_stats:
            stats = processing_stats[0]
            return {
                "average_processing_hours": round(stats["avg_processing_time"], 2),
                "min_processing_hours": round(stats["min_processing_time"], 2),
                "max_processing_hours": round(stats["max_processing_time"], 2),
                "sample_size": stats["count"]
            }
        else:
            return {
                "average_processing_hours": 0,
                "min_processing_hours": 0,
                "max_processing_hours": 0,
                "sample_size": 0
            }
    
    async def get_blockchain_analytics(self) -> Dict[str, Any]:
        """Get blockchain-specific analytics"""
        # Count of blockchain-verified records
        blockchain_verified_count = await self.db.transcript_requests.count_documents({
            "content_hash": {"$exists": True, "$ne": ""}
        })
        
        # Total records
        total_records = await self.db.transcript_requests.count_documents({})
        
        # Recent blockchain activity (last 7 days)
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        recent_blockchain_activity = await self.db.transcript_requests.count_documents({
            "content_hash": {"$exists": True, "$ne": ""},
            "created_at": {"$gte": seven_days_ago}
        })
        
        # Blockchain adoption rate
        adoption_rate = (blockchain_verified_count / total_records * 100) if total_records > 0 else 0
        
        return {
            "total_blockchain_records": blockchain_verified_count,
            "total_records": total_records,
            "adoption_rate": round(adoption_rate, 2),
            "recent_activity_7days": recent_blockchain_activity,
            "immutable_verifications": blockchain_verified_count,
            "tamper_proof_rate": round(adoption_rate, 2)  # Same as adoption rate
        }
    
    async def get_user_activity_metrics(self) -> Dict[str, Any]:
        """Get user activity and engagement metrics"""
        # Count users by role
        user_stats = await self.db.users.aggregate([
            {"$group": {
                "_id": "$role",
                "count": {"$sum": 1}
            }}
        ]).to_list(None)
        
        user_counts = {item["_id"]: item["count"] for item in user_stats}
        
        # Recent user registrations (last 30 days)
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        recent_registrations = await self.db.users.count_documents({
            "created_at": {"$gte": thirty_days_ago}
        })
        
        # Active users (those with recent activity)
        active_students = await self.db.transcript_requests.distinct("student_id", {
            "created_at": {"$gte": thirty_days_ago}
        })
        
        return {
            "total_users": sum(user_counts.values()),
            "students": user_counts.get("student", 0),
            "issuers": user_counts.get("issuer", 0),
            "verifiers": user_counts.get("verifier", 0),
            "recent_registrations": recent_registrations,
            "active_students_30days": len(active_students)
        }
    
    async def get_real_time_alerts(self) -> Dict[str, Any]:
        """Get real-time system alerts and notifications"""
        # Pending requests requiring attention
        pending_requests = await self.db.transcript_requests.count_documents({
            "status": "pending"
        })
        
        # Overdue requests (pending for more than 48 hours)
        two_days_ago = datetime.now(timezone.utc) - timedelta(hours=48)
        overdue_requests = await self.db.transcript_requests.count_documents({
            "status": "pending",
            "created_at": {"$lte": two_days_ago}
        })
        
        # Failed blockchain transactions (if any tracking is implemented)
        # This would require additional tracking in the system
        
        alerts = []
        
        if pending_requests > 10:
            alerts.append({
                "type": "warning",
                "message": f"{pending_requests} transcript requests pending verification",
                "action": "Review pending requests in issuer dashboard",
                "priority": "medium"
            })
        
        if overdue_requests > 0:
            alerts.append({
                "type": "urgent",
                "message": f"{overdue_requests} requests overdue (>48h pending)",
                "action": "Immediate attention required for overdue requests",
                "priority": "high"
            })
        
        return {
            "pending_requests": pending_requests,
            "overdue_requests": overdue_requests,
            "active_alerts": alerts,
            "system_health": "healthy" if len(alerts) == 0 else "attention_needed"
        }
    
    async def get_comprehensive_dashboard_data(self) -> Dict[str, Any]:
        """Get all analytics data for the admin dashboard"""
        return {
            "overview": await self.get_verification_overview(),
            "trends": await self.get_daily_trends(),
            "universities": await self.get_university_analytics(),
            "processing_times": await self.get_processing_time_analytics(),
            "blockchain": await self.get_blockchain_analytics(),
            "users": await self.get_user_activity_metrics(),
            "alerts": await self.get_real_time_alerts(),
            "generated_at": datetime.now(timezone.utc).isoformat()
        }

# This will be initialized with the database instance
analytics_service = None

def initialize_analytics_service(db: AsyncIOMotorDatabase):
    """Initialize the analytics service with database instance"""
    global analytics_service
    analytics_service = AnalyticsService(db)