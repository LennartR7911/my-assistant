import threading
import time
import logging
import sys
from src.core.config import settings
from src.services.input_handler import start_input_watcher
from src.services.task_enricher import TaskEnricher
from src.services.daily_setup import generate_daily_log
from src.services.project_manager import create_project

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run_enricher():
    enricher = TaskEnricher()
    enricher.run_loop()

def main():
    logger.info("Starting Life OS...")

    # 1. Run Daily Log Check
    try:
        generate_daily_log()
    except Exception as e:
        logger.error(f"Daily log generation failed: {e}")

    # 2. Start Input Watcher
    observer = start_input_watcher()

    # 3. Start Task Enricher (in thread)
    enricher_thread = threading.Thread(target=run_enricher, daemon=True)
    enricher_thread.start()

    # 4. CLI Loop
    try:
        while True:
            print("\n--- Life OS Menu ---")
            print("1. Create New Project")
            print("2. Help & Instructions")
            print("3. Exit")
            choice = input("Enter choice: ").strip()

            if choice == "1":
                name = input("Project Name: ").strip()
                client = input("Client Name: ").strip()
                if name and client:
                    create_project(name, client)
                else:
                    print("Invalid input.")
            elif choice == "2":
                print("\n" + "="*50)
                print("   Life OS Quick Start Guide")
                print("="*50)
                print("1. Sync Tasks: Tasks sync automatically every 60s via GitHub.")
                print("2. Create Project: Use Option 1 to scaffold folders.")
                print("3. Input: Drop .mp3 or .txt files into 'Inbox/' folder.")
                print("4. Daily Log: Check 'Logs/' folder for today's tasks.")
                print("="*50 + "\n")
            elif choice == "3":
                logger.info("Shutting down...")
                observer.stop()
                observer.join()
                break
            else:
                print("Invalid choice.")

    except KeyboardInterrupt:
        observer.stop()
        observer.join()
        logger.info("Stopped via KeyboardInterrupt")

if __name__ == "__main__":
    main()
