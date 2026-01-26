"""
Celery Application Configuration
Background task queue using Redis as broker
"""

import os
import logging
from celery import Celery
from kombu import Exchange, Queue

logger = logging.getLogger(__name__)

# Get Redis URL from environment (same as cache)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Celery app
celery_app = Celery(
    "aanchal_ai",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "tasks.ai_tasks",
        "tasks.notification_tasks",
        "tasks.report_tasks"
    ]
)

# Celery configuration
celery_app.conf.update(
    # Serialization
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    
    # Timezone
    timezone="Asia/Kolkata",
    enable_utc=True,
    
    # Task execution settings
    task_acks_late=True,  # Acknowledge after task completion
    task_reject_on_worker_lost=True,  # Reject task if worker dies
    worker_prefetch_multiplier=4,  # Number of tasks to prefetch
    
    # Retry settings
    task_default_retry_delay=60,  # 1 minute default retry delay
    task_max_retries=3,
    
    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    result_extended=True,  # Store additional task info
    
    # Task routing
    task_default_queue="default",
    task_queues=(
        Queue("default", Exchange("default"), routing_key="default"),
        Queue("ai_tasks", Exchange("ai_tasks"), routing_key="ai.#"),
        Queue("notifications", Exchange("notifications"), routing_key="notify.#"),
        Queue("reports", Exchange("reports"), routing_key="report.#"),
    ),
    
    # Task routes
    task_routes={
        "tasks.ai_tasks.*": {"queue": "ai_tasks", "routing_key": "ai.task"},
        "tasks.notification_tasks.*": {"queue": "notifications", "routing_key": "notify.task"},
        "tasks.report_tasks.*": {"queue": "reports", "routing_key": "report.task"},
    },
    
    # Worker settings
    worker_concurrency=4,  # Number of worker processes
    worker_max_tasks_per_child=1000,  # Restart worker after N tasks
    
    # Beat scheduler (for periodic tasks)
    beat_schedule={
        "check-pending-reminders": {
            "task": "tasks.notification_tasks.check_pending_reminders",
            "schedule": 3600.0,  # Every hour
        },
        "cleanup-old-results": {
            "task": "tasks.ai_tasks.cleanup_old_results",
            "schedule": 86400.0,  # Daily
        },
    },
)

# Log configuration
logger.info(f"✅ Celery configured with broker: {REDIS_URL[:30]}...")
