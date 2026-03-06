# bank.py
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd

DEFAULT_FILE = Path("BankOps.xlsx")
SHEET = "accounts"

@dataclass
class Customer:
    name: str
    aadhar: str
    contact: str

@dataclass
class Account:
    acc_no: int
    name: str
    balance: float
    pin: str
    status: str = "active"

class Bank:
    """
    Minimal Bank using Excel (.xlsx) via pandas.
    One sheet: accounts with columns (acc_no, name, balance, pin, status)
    """
    def __init__(self, file_path: str | Path = DEFAULT_FILE):
        self.file_path = Path(file_path)
        self._ensure_file()

    # ---------- storage helpers ----------
    def _ensure_file(self):
        if not self.file_path.exists():
            df = pd.DataFrame(columns=["acc_no", "name", "balance", "pin", "status"])
            with pd.ExcelWriter(self.file_path, engine="openpyxl", mode="w") as w:
                df.to_excel(w, sheet_name=SHEET, index=False)

    def _read_df(self) -> pd.DataFrame:
        return pd.read_excel(self.file_path, sheet_name=SHEET, engine="openpyxl")

    def _write_df(self, df: pd.DataFrame):
        with pd.ExcelWriter(self.file_path, engine="openpyxl", mode="w") as w:
            df.to_excel(w, sheet_name=SHEET, index=False)

    def _next_acc_no(self, df: pd.DataFrame) -> int:
        if df.empty:
            return 1001
        return int(df["acc_no"].max()) + 1

    # ---------- simple utilities using comprehensions ----------
    def list_active_accounts(self) -> List[int]:
        """Return a list of active account numbers (list comprehension)."""
        df = self._read_df()
        if df.empty:
            return []
        active_rows = df[df["status"] == "active"]
        return [int(a) for a in active_rows["acc_no"].tolist()]

    def account_summary(self) -> Dict[int, float]:
        """Return {acc_no: balance} only for active accounts (dict comprehension)."""
        df = self._read_df()
        if df.empty:
            return {}
        active = df[df["status"] == "active"][["acc_no", "balance"]]
        return {int(r["acc_no"]): float(r["balance"]) for _, r in active.iterrows()}

    # ---------- operations (kept basic) ----------
    def create_account(self, customer: Customer, pin: str, initial: float = 0.0) -> int:
        if initial < 0:
            raise ValueError("Initial deposit must be >= 0.")
        df = self._read_df()
        acc_no = self._next_acc_no(df)
        new_row = {
            "acc_no": acc_no,
            "name": customer.name,
            "balance": float(initial),
            "pin": str(pin),
            "status": "active",
        }
        df.loc[len(df)] = new_row
        #df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        self._write_df(df)
        return acc_no

    def deposit(self, acc_no: int, amount: float) -> float:
        if amount <= 0:
            raise ValueError("Amount must be > 0.")
        df = self._read_df()
        row = df.loc[df["acc_no"] == acc_no]
        if row.empty:
            raise ValueError("Account not found.")
        if row.iloc[0]["status"] != "active":
            raise ValueError("Account not active.")
        new_bal = float(row.iloc[0]["balance"]) + float(amount)
        df.loc[df["acc_no"] == acc_no, "balance"] = new_bal
        self._write_df(df)
        return new_bal

    def withdraw(self, acc_no: int, pin: str, amount: float):
        if amount <= 0:
            raise ValueError("Amount must be > 0.")
        df = self._read_df()
        row = df.loc[df["acc_no"] == acc_no]
        if row.empty:
            return "Account not found"
        if str(row.iloc[0]["pin"]) != str(pin):
            return "Invalid PIN"
        if row.iloc[0]["status"] != "active":
            return "Account not active"
        bal = float(row.iloc[0]["balance"])
        if amount > bal:
            return "Insufficient Balance"
        new_bal = bal - float(amount)
        df.loc[df["acc_no"] == acc_no, "balance"] = new_bal
        self._write_df(df)
        return new_bal

    def get_balance(self, acc_no: int, pin: str):
        df = self._read_df()
        row = df.loc[df["acc_no"] == acc_no]
        if row.empty:
            return "Account not found"
        if str(row.iloc[0]["pin"]) != str(pin):
            return "Invalid PIN"
        return float(row.iloc[0]["balance"])

    def close_account(self, acc_no: int, pin: str) -> str:
        df = self._read_df()
        row = df.loc[df["acc_no"] == acc_no]
        if row.empty:
            return "Account not found"
        if str(row.iloc[0]["pin"]) != str(pin):
            return "Invalid PIN"
        df.loc[df["acc_no"] == acc_no, "status"] = "closed"
        self._write_df(df)
        return "Closed"
