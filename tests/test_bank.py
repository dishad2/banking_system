# tests/test_bank.py
from pathlib import Path
from bank import Bank, Customer

def mk_bank(tmp_path: Path) -> Bank:
    # Each test uses a fresh Excel file
    file = tmp_path / "BankOps.xlsx"
    return Bank(file_path=file)

def test_create_and_balance(tmp_path):
    bank = mk_bank(tmp_path)
    acc = bank.create_account(Customer("Alice", "1111", "99999"), pin="1234", initial=200.0)
    assert isinstance(acc, int)
    assert bank.get_balance(acc, "1234") == 200.0

def test_deposit_and_withdraw(tmp_path):
    bank = mk_bank(tmp_path)
    acc = bank.create_account(Customer("Bob", "2222", "88888"), pin="4321", initial=100.0)
    assert bank.deposit(acc, 50.0) == 150.0
    assert bank.withdraw(acc, "4321", 40.0) == 110.0
    assert bank.get_balance(acc, "4321") == 110.0

def test_invalid_pin_and_insufficient_and_close(tmp_path):
    bank = mk_bank(tmp_path)
    acc = bank.create_account(Customer("Carol", "3333", "77777"), pin="9999", initial=40.0)
    assert bank.get_balance(acc, "0000") == "Invalid PIN"
    assert bank.withdraw(acc, "9999", 100.0) == "Insufficient Balance"
    assert bank.close_account(acc, "9999") == "Closed"