import schedule
import time
import os

def job():
    os.system('python fetch_and_clean_data.py')

# Schedule the job every day at a specific time (e.g., 00:00)
schedule.every().day.at("00:00").do(job)

while True:
    schedule.run_pending()
    time.sleep(60)
