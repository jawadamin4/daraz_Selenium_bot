import schedule
import time
from main import my_bot


schedule.every().tuesday.at("09:00").do(my_bot)


while True:
    schedule.run_pending()
    time.sleep(1)