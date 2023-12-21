import schedule
import time
from datetime import datetime, timedelta
import logging
from pathlib import Path

from extras import binance_feed

# Absolute path to the directory of the current file
dir_path = Path(__file__).resolve().parent

# Create a logs directory if it doesn't exist
log_dir = dir_path / 'logs'
log_dir.mkdir(exist_ok=True)

# Set up logging to a file in the logs directory
log_file = log_dir / 'binance_refresh.log'
logging.basicConfig(filename=log_file, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def binance_feed_job():
    start_time = datetime.now()
    print(f"Job started at local time: {start_time}")
    logging.info(f"Job started at local time: {start_time}")

    try:
        binance_feed.connect_to_binance()
        end_time = datetime.now()
        print(f"Job finished at local time: {end_time}")
        logging.info(f"Job finished at local time: {end_time}")
    except Exception as e:
        print(f"Failed to run job: {str(e)}")
        logging.error(f"Failed to run job: {str(e)}")

# Run the job once as soon as the script is launched
binance_feed_job()

# Schedule job to run at 00:10 UTC time every day
schedule.every().day.at("00:10").do(binance_feed_job)

while True:
    # Get current time in UTC
    current_time = datetime.utcnow()
    print('Current Time :', current_time)

    # Calculate difference in seconds to next 00:10 UTC
    next_job_time = current_time.replace(hour=0, minute=10, second=0, microsecond=0)
    if current_time >= next_job_time:
        next_job_time += timedelta(days=1)
    time_to_start = (next_job_time - current_time).total_seconds()
    print('Seconds to start :', time_to_start)
    # Sleep until it's time to run the job
    time.sleep(time_to_start)

    # Run all jobs
    schedule.run_all()