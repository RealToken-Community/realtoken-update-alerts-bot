#!/bin/bash
set -e

# ----------------------------------------
# Realtoken Update Alerts bot Docker Entrypoint
# ----------------------------------------
# Responsibilities:
# 1. Verify that BOT_REALTOKENS_UPDATE_ALERTS_TOKEN is set.
# 2. Start the bot.
# ----------------------------------------

echo "Starting Realtoken Update Alerts bot container..."

# Move into the application directory (must match WORKDIR in Dockerfile)
cd /app

# 1) Ensure BOT_REALTOKENS_UPDATE_ALERTS_TOKEN is provided
if [ -z "$BOT_REALTOKENS_UPDATE_ALERTS_TOKEN" ]; then
  echo "ERROR: environment variable BOT_REALTOKENS_UPDATE_ALERTS_TOKEN is not set."
  echo "Please define it in your .env file"
  exit 1
fi


# 2) Start the bot
echo "Launching Realtoken Update Alerts bot..."
exec python3 -m bot.main