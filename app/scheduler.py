import os
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timezone, timedelta
from app.sheets import read_all_items, update_row_by_sku, append_po_log
from app.mailer import send_owner_email

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OWNER_EMAIL = os.environ.get('OWNER_EMAIL')
MIN_LAST_CHECK_HOURS = int(os.environ.get('MIN_LAST_CHECK_HOURS', 24))

def check_inventory_once():
    logger.info('Running inventory check at %s', datetime.now(timezone.utc).isoformat())
    items = read_all_items()
    now = datetime.now(timezone.utc)
    for item in items:
        try:
            if item['on_hand_qty'] <= item['reorder_threshold']:
                # check last_checked
                last_checked = item.get('last_checked')
                if last_checked:
                    try:
                        last_dt = datetime.fromisoformat(last_checked)
                    except Exception:
                        last_dt = None
                else:
                    last_dt = None

                if last_dt and (now - last_dt) < timedelta(hours=MIN_LAST_CHECK_HOURS):
                    logger.info('Skipping %s — checked recently', item['sku'])
                    continue

                # Needs human approval — send owner email
                logger.info('Sending approval request for %s', item['sku'])
                send_owner_email(OWNER_EMAIL, item)
                # we don't update last_checked until owner acts
        except Exception as e:
            logger.exception('Error processing %s: %s', item.get('sku'), e)

scheduler = BackgroundScheduler()

def start_scheduler():
    interval_hours = int(os.environ.get('CHECK_HOURS', 1))
    scheduler.add_job(check_inventory_once, 'interval', hours=interval_hours, next_run_time=datetime.now())
    scheduler.start()
    logger.info('Scheduler started — interval: %d hours', interval_hours)

if __name__ == '__main__':
    start_scheduler()
    import time
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        scheduler.shutdown()
