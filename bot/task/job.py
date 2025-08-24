from __future__ import annotations
from telegram.ext import Application
from bot.core import run_update_cycle_and_notify
from bot.task.update_realtoken_owned import update_realtoken_owned

async def job_update_and_notify(context) -> None:
    """JobQueue wrapper that calls the business logic orchestrator."""
    app: Application = context.application
    await run_update_cycle_and_notify(app)

async def job_update_realtoken_owned(context) -> None:
    """JobQueue wrapper that calls the business logic orchestrator."""
    app: Application = context.application
    await update_realtoken_owned(app)