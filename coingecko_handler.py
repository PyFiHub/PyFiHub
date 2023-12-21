import schedule
import time
from datetime import datetime, timedelta
import logging
from pathlib import Path

from extras import coingecko_feed

# Absolute path to the directory of the current file
dir_path = Path(__file__).resolve().parent

# Create a logs directory if it doesn't exist
log_dir = dir_path / 'logs'
log_dir.mkdir(exist_ok=True)

# Set up logging to a file in the logs directory
log_file = log_dir / 'coingecko_refresh.log'
logging.basicConfig(filename=log_file, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def coingecko_feed_job():
    start_time = datetime.now()
    print(f"Job started at local time: {start_time}")
    logging.info(f"Job started at local time: {start_time}")

    try:
        coingecko_feed.connect_to_coingecko()
        end_time = datetime.now()
        print(f"Job finished at local time: {end_time}")
        logging.info(f"Job finished at local time: {end_time}")
    except Exception as e:
        print(f"Failed to run job: {str(e)}")
        logging.error(f"Failed to run job: {str(e)}")

# Call the job function directly to run it immediately when the script is launched
coingecko_feed_job()

# Schedule the job to run every 15 minutes
schedule.every(15).minutes.do(coingecko_feed_job)

while True:
    # Run all jobs that are scheduled to run
    schedule.run_pending()
    
    # Sleep for 5 minutes before checking again for pending jobs
    # This matches your job interval, reducing unnecessary checks
    time.sleep(15*60)  # sleep for 15 minutes
