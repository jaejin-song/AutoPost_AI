import yaml
import os

def load_accounts(path="accounts.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("account_sets", {})

def load_env():
    from dotenv import load_dotenv
    load_dotenv()
    return {
        "NEWS_API_KEY": os.getenv("NEWS_API_KEY"),
        "GOOGLE_SHEET_KEY": os.getenv("GOOGLE_SHEET_KEY"),
        "GOOGLE_SERVICE_ACCOUNT_FILE": os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE"),
    }
