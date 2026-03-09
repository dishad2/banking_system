# bank.py
from abc import ABC, abstractmethod
from pathlib import Path
import pandas as pd

DEFAULT_FILE = Path("BankOps.xlsx")
SHEET = "accounts"

class Customer:
    def __init__(self, name, aadhar, contact):
        self.name = name
        a = str(aadhar).strip()
        c = str(contact).strip()

        if not (a.isdigit() and len(a) == 12):
                raise ValueError("Aadhaar must be exactly 12 digits.")

        if not (c.isdigit() and len(c) == 10):
                raise ValueError("Contact must be exactly 10 digits.")
        
        self.aadhar = aadhar
        self.contact = contact


    def __repr__(self):
        return f"Customer(name={self.name}, aadhar={self.aadhar}, contact={self.contact})"


class BaseAccount(ABC):

    def __init__(self, acc_no, name, balance, pin, status="active"):
        self.bank_country = "India"

        self.acc_no = acc_no
        self.name = name
        self.balance = float(balance)
        self.pin = str(pin)
        self.status = status 

    def deposit(self, amount):
        if amount <= 0:
            raise ValueError("Amount must be > 0.")
        if self.status != "active":
            raise ValueError("Account not active.")
        self.balance += float(amount)
        return self.balance

    @abstractmethod
    def withdraw(self, pin, amount):
        pass

    def check_pin(self, pin):
        return str(self.pin) == str(pin)

    def is_active(self):
        return self.status == "active"

    def close(self):
        self.status = "closed"
        return "Closed"

    @classmethod
    def bank_origin(cls):
        return "India"

    def __repr__(self):
        return f"Account(acc_no={self.acc_no}, name={self.name}, balance={self.balance}, status={self.status})"


class SavingsAccount(BaseAccount):

    def withdraw(self, pin, amount):
        if amount <= 0:
            raise ValueError("Amount must be > 0.")
        if not self.is_active():
            return "Account not active"
        if not self.check_pin(pin):
            return "Invalid PIN"
        if amount > self.balance:
            return "Insufficient Balance"
        self.balance -= float(amount)
        return self.balance

class Bank:

    def __init__(self, file_path=DEFAULT_FILE):
        self.file_path = Path(file_path)
        self._ensure_file()

    def _ensure_file(self):
        if not self.file_path.exists():
            df = pd.DataFrame(columns=["acc_no", "name", "balance", "pin", "status", "type"])
            with pd.ExcelWriter(self.file_path, engine="openpyxl", mode="w") as w:
                df.to_excel(w, sheet_name=SHEET, index=False)

    def _read_df(self):
        return pd.read_excel(self.file_path, sheet_name=SHEET, engine="openpyxl")

    def _write_df(self, df):
        with pd.ExcelWriter(self.file_path, engine="openpyxl", mode="w") as w:
            df.to_excel(w, sheet_name=SHEET, index=False)

    def _next_acc_no(self, df):
        if df.empty:
            return 1001
        return int(df["acc_no"].max()) + 1

    def _make_account(self, row):
        acc_no = int(row["acc_no"])
        name = row["name"]
        balance = float(row["balance"])
        pin = str(row["pin"])
        status = row.get("status", "active")
        atype = row.get("type", "SAVINGS")

        return SavingsAccount(acc_no, name, balance, pin, status)

    def list_active_accounts(self):
        df = self._read_df()
        if df.empty:
            return []
        active_rows = df[df["status"] == "active"]
        return [int(a) for a in active_rows["acc_no"].tolist()]

    def account_summary(self):
        df = self._read_df()
        if df.empty:
            return {}
        active = df[df["status"] == "active"][["acc_no", "balance"]]
        return {int(r["acc_no"]): float(r["balance"]) for _, r in active.iterrows()}

    def create_account(self, customer, pin, initial=0.0, account_type="SAVINGS"):
        if initial < 0:
            raise ValueError("Initial deposit must be >= 0.")
        
        pin_str = str(pin).strip()
        if not (pin_str.isdigit() and len(pin_str) == 4):
            raise ValueError("PIN must be exactly 4 digits.")

        df = self._read_df()
        acc_no = self._next_acc_no(df)
        new_row = {
            "acc_no": acc_no,
            "name": customer.name,
            "balance": float(initial),
            "pin": str(pin),
            "status": "active",
            "type": account_type,
        }
        df.loc[len(df)] = new_row
        self._write_df(df)
        return acc_no

    def _load_account(self, acc_no):
        df = self._read_df()
        row = df.loc[df["acc_no"] == acc_no]
        if row.empty:
            return None, df
        return self._make_account(row.iloc[0]), df

    def deposit(self, acc_no, amount):
        if amount <= 0:
            raise ValueError("Amount must be > 0.")
        account, df = self._load_account(acc_no)
        if account is None:
            raise ValueError("Account not found.")
        if not account.is_active():
            raise ValueError("Account not active.")
        new_bal = account.deposit(amount)
        df.loc[df["acc_no"] == acc_no, "balance"] = float(new_bal)
        self._write_df(df)
        return new_bal

    def withdraw(self, acc_no, pin, amount):
        account, df = self._load_account(acc_no)
        if account is None:
            return "Account not found"
        res = account.withdraw(pin, amount)
        if isinstance(res, str):
            return res
        df.loc[df["acc_no"] == acc_no, "balance"] = float(res)
        self._write_df(df)
        return res

    def get_balance(self, acc_no, pin):
        account, _ = self._load_account(acc_no)
        if account is None:
            return "Account not found"
        if not account.check_pin(pin):
            return "Invalid PIN"
        return float(account.balance)

    def close_account(self, acc_no, pin):
        account, df = self._load_account(acc_no)
        if account is None:
            return "Account not found"
        if not account.check_pin(pin):
            return "Invalid PIN"
        status = account.close()
        df.loc[df["acc_no"] == acc_no, "status"] = account.status
        self._write_df(df)
        return status