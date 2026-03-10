# tests/test_bank.py
from pathlib import Path
from bank import Bank, Customer

def mk_bank(tmp_path: Path) -> Bank:
    file = tmp_path / "BankOps.xlsx"
    return Bank(file_path=file)

def test_create_and_balance(tmp_path):
    bank = mk_bank(tmp_path)
    acc = bank.create_account(Customer("Alice", "111122223333", "9999911111"), pin="1234", initial=200.0)
    assert isinstance(acc, int)
    assert bank.get_balance(acc, "1234") == 200.0

def test_deposit_and_withdraw(tmp_path):
    bank = mk_bank(tmp_path)
    acc = bank.create_account(Customer("Bob", "222233334444", "8888822222"), pin="4321", initial=100.0)
    assert bank.deposit(acc, 50.0) == 150.0
    assert bank.withdraw(acc, "4321", 40.0) == 110.0
    assert bank.get_balance(acc, "4321") == 110.0

def test_invalid_pin_and_insufficient_and_close(tmp_path):
    bank = mk_bank(tmp_path)
    acc = bank.create_account(Customer("Carol", "333344445555", "7777744444"), pin="9999", initial=40.0)
    assert bank.get_balance(acc, "0000") == "Invalid PIN"
    assert bank.withdraw(acc, "9999", 100.0) == "Insufficient Balance"
    assert bank.close_account(acc, "9999") == "Closed"

def test_validation_errors(tmp_path):
    bank = mk_bank(tmp_path)

    # Aadhaar invalid
    import pytest
    with pytest.raises(ValueError, match="Aadhaar"):
        Customer("X", "123", "9876543210")

    # Contact invalid
    with pytest.raises(ValueError, match="Contact"):
        Customer("X", "111122223333", "12345")

    # PIN invalid
    with pytest.raises(ValueError, match="PIN"):
        bank.create_account(Customer("Y", "111122223333", "9876543210"), pin="12", initial=0)