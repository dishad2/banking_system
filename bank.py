# bank.py
from abc import ABC, abstractmethod
from pathlib import Path
import threading
import pandas as pd

DEFAULT_FILE = Path("BankOps.xlsx")
SHEET = "accounts"

PIN_LEN = 4
AADHAAR_LEN = 12
CONTACT_LEN = 10
ACC_MIN_LEN = 4
VALID_ACCOUNT_TYPES = {"SAVINGS", "CURRENT"}


def is_digits(value: str, length: int = None, min_len: int = None, max_len: int = None) -> bool:
    if value is None:
        return False
    v = str(value).strip()
    if not v.isdigit():
        return False
    if length is not None and len(v) != length:
        return False
    if min_len is not None and len(v) < min_len:
        return False
    if max_len is not None and len(v) > max_len:
        return False
    return True

def must_be_digits(value: str, field: str, length: int = None, min_len: int = None, max_len: int = None):
    if not is_digits(value, length, min_len, max_len):
        if length:
            raise ValueError(f"{field} must be exactly {length} digits.")
        rng = []
        if min_len: rng.append(f"≥{min_len}")
        if max_len: rng.append(f"≤{max_len}")
        rng_desc = f" ({' and '.join(rng)} digits)" if rng else ""
        raise ValueError(f"{field} must contain only digits{rng_desc}.")

def must_be_nonempty(text: str, field: str):
    if not str(text).strip():
        raise ValueError(f"{field} cannot be empty.")

def must_be_amount(value: str | float, positive_only=True, allow_zero=True):
    try:
        amt = float(value)
    except Exception:
        raise ValueError("Amount must be a valid number.")
    if positive_only and amt < 0:
        raise ValueError("Amount must be ≥ 0.")
    if not allow_zero and amt <= 0:
        raise ValueError("Amount must be > 0.")
    return amt


class Customer:
    def __init__(self, name, address, aadhar, contact):
        must_be_nonempty(name, "Name")
        must_be_nonempty(address, "Address")
        must_be_digits(aadhar, "Aadhaar", length=AADHAAR_LEN)
        must_be_digits(contact, "Contact", length=CONTACT_LEN)
        self.name = str(name).strip()
        self.address = str(address).strip()
        self.aadhar = str(aadhar).strip()
        self.contact = str(contact).strip()

    def __repr__(self):
        return f"Customer(name={self.name}, aadhar={self.aadhar}, contact={self.contact})"


class BaseAccount(ABC):
    def __init__(self, acc_no, name, balance, pin, status="active", atype="SAVINGS"):
        self.bank_country = "India"
        self.acc_no = int(acc_no)
        self.name = str(name)
        self.balance = float(balance)
        must_be_digits(pin, "PIN", length=PIN_LEN)
        self.pin = str(pin)
        self.status = str(status)
        self.atype = str(atype).upper()

    def deposit(self, amount):
        amt = must_be_amount(amount, positive_only=True, allow_zero=False)
        if self.status != "active":
            raise ValueError("Account not active.")
        self.balance += float(amt)
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


class SavingsAccount(BaseAccount):
    def withdraw(self, pin, amount):
        amt = must_be_amount(amount, positive_only=True, allow_zero=False)
        if not self.is_active():
            return "Account not active"
        if not self.check_pin(pin):
            return "Invalid PIN"
        if amt > self.balance:
            return "Insufficient Balance"
        self.balance -= float(amt)
        return self.balance


class Bank:
    def __init__(self, file_path=DEFAULT_FILE):
        self.file_path = Path(file_path)
        self.lock = threading.Lock()
        self._ensure_file()

    def _ensure_file(self):
        if not self.file_path.exists():
            cols = ["acc_no", "name", "address", "aadhar", "contact",
                    "balance", "pin", "status", "type"]
            df = pd.DataFrame(columns=cols)
            with pd.ExcelWriter(self.file_path, engine="openpyxl", mode="w") as w:
                df.to_excel(w, sheet_name=SHEET, index=False)

    def _read_df(self):
        with self.lock:
            return pd.read_excel(self.file_path, sheet_name=SHEET, engine="openpyxl")

    def _write_df(self, df):
        with self.lock:
            with pd.ExcelWriter(self.file_path, engine="openpyxl", mode="w") as w:
                df.to_excel(w, sheet_name=SHEET, index=False)

    def _next_acc_no(self, df):
        if df.empty:
            return 1001
        return int(df["acc_no"].max()) + 1

    def _make_account(self, row):
        return SavingsAccount(
            acc_no=int(row["acc_no"]),
            name=row["name"],
            balance=float(row["balance"]),
            pin=str(row["pin"]),
            status=row.get("status", "active"),
            atype=row.get("type", "SAVINGS"),
        )

    # ---------- existence helpers ----------
    def account_exists(self, acc_no: int) -> bool:
        try:
            acc_no = int(acc_no)
        except Exception:
            return False
        df = self._read_df()
        if df.empty:
            return False
        return not df.loc[df["acc_no"] == acc_no].empty

    def require_account(self, acc_no: int):
        if not self.account_exists(acc_no):
            raise ValueError("Account does not exist.")

    # ---------- public operations ----------
    def create_account(self, customer: Customer, pin: str, initial=0.0, account_type="SAVINGS"):
        pin_str = str(pin).strip()
        must_be_digits(pin_str, "PIN", length=PIN_LEN)
        atype = str(account_type or "SAVINGS").upper()
        if atype not in VALID_ACCOUNT_TYPES:
            raise ValueError(f"Account type must be one of {sorted(VALID_ACCOUNT_TYPES)}.")
        init = must_be_amount(initial, positive_only=True, allow_zero=True)

        df = self._read_df()
        acc_no = self._next_acc_no(df)

        new_row = {
            "acc_no": acc_no,
            "name": customer.name,
            "address": customer.address,
            "aadhar": customer.aadhar,
            "contact": customer.contact,
            "balance": float(init),
            "pin": pin_str,
            "status": "active",
            "type": atype,
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

    def deposit(self, acc_no, pin, amount):
        # Validate formats
        must_be_digits(str(acc_no), "Account Number", min_len=ACC_MIN_LEN)
        must_be_digits(str(pin), "PIN", length=PIN_LEN)
        amt = must_be_amount(amount, positive_only=True, allow_zero=False)

        # Load and validate business state
        account, df = self._load_account(int(acc_no))
        if account is None:
            return "Account not found"
        if not account.is_active():
            return "Account not active"
        if not account.check_pin(pin):
            return "Invalid PIN"

        new_bal = account.deposit(amt)
        df.loc[df["acc_no"] == account.acc_no, "balance"] = float(new_bal)
        self._write_df(df)
        return new_bal

    def withdraw(self, acc_no, pin, amount):
        must_be_digits(str(acc_no), "Account Number", min_len=ACC_MIN_LEN)
        must_be_digits(str(pin), "PIN", length=PIN_LEN)
        account, df = self._load_account(int(acc_no))
        if account is None:
            return "Account not found"
        res = account.withdraw(pin, amount)
        if isinstance(res, str):
            return res
        df.loc[df["acc_no"] == account.acc_no, "balance"] = float(res)
        self._write_df(df)
        return res

    def get_balance(self, acc_no, pin):
        must_be_digits(str(acc_no), "Account Number", min_len=ACC_MIN_LEN)
        must_be_digits(str(pin), "PIN", length=PIN_LEN)
        account, _ = self._load_account(int(acc_no))
        if account is None:
            return "Account not found"
        if not account.check_pin(pin):
            return "Invalid PIN"
        return float(account.balance)

    def close_account(self, acc_no, pin):
        must_be_digits(str(acc_no), "Account Number", min_len=ACC_MIN_LEN)
        must_be_digits(str(pin), "PIN", length=PIN_LEN)
        account, df = self._load_account(int(acc_no))
        if account is None:
            return "Account not found"
        if not account.check_pin(pin):
            return "Invalid PIN"
        status = account.close()
        df.loc[df["acc_no"] == account.acc_no, "status"] = account.status
        self._write_df(df)
        return status

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