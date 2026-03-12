import math
import os
import re
import pandas as pd
import pytest

from bank import (
    Bank,
    Customer,
    PIN_LEN,
    AADHAAR_LEN,
    CONTACT_LEN,
    ACC_MIN_LEN,
    is_digits,
    must_be_digits,
    must_be_nonempty,
)

# Fixtures & helpers

@pytest.fixture()
def bank_tmp(tmp_path):
    # Create a fresh bank storage per test
    fp = tmp_path / "BankOps.xlsx"
    b = Bank(file_path=fp)
    return b


def open_account(b: Bank,
                 name="Alice",
                 address="Pune",
                 aadhar="123456789012",
                 contact="9876543210",
                 pin="1234",
                 initial=1000.0,
                 atype="SAVINGS"):
    cust = Customer(name, address, aadhar, contact)
    acc = b.create_account(cust, pin, initial, atype)
    return acc

# Validation helper tests


@pytest.mark.parametrize(
    "value,length,min_len,expected",
    [
        ("1234", 4, None, True),           # numeric exact
        ("12345", 4, None, False),         # wrong exact length
        ("1234", None, 4, True),           # min len satisfied
        ("12", None, 4, False),            # min len not satisfied
        ("12a4", 4, None, False),          # alphanumeric
        ("12#4", 4, None, False),          # numeric + special
        ("####", 4, None, False),          # only special
        ("", None, 1, False),              # empty
        (None, 4, None, False),             # None
        ("   1234   ", 4, None, True),     # whitespace padded
    ]
)
def test_is_digits_various(value, length, min_len, expected):
    assert is_digits(value, length=length, min_len=min_len) is expected


@pytest.mark.parametrize(
    "value,kw",
    [
        ("12a4", {"field": "X", "length": 4}),
        ("12#4", {"field": "X", "length": 4}),
        ("####", {"field": "X", "length": 4}),
        ("12",   {"field": "X", "min_len": 4}),
        ("",     {"field": "X", "min_len": 1}),
        (None,   {"field": "X", "min_len": 1}),
    ]
)
def test_must_be_digits_raises(value, kw):
    with pytest.raises(ValueError):
        must_be_digits(value, **kw)


def test_must_be_nonempty_raises():
    with pytest.raises(ValueError):
        must_be_nonempty("   ", "Field")

# Customer validation

def test_customer_valid():
    c = Customer("Bob", "Addr", "1" * AADHAAR_LEN, "9" * CONTACT_LEN)
    assert c.name == "Bob" and c.aadhar == "1" * AADHAAR_LEN


@pytest.mark.parametrize(
    "kwargs",
    [
        {"name": "", "address": "A", "aadhar": "1" * AADHAAR_LEN, "contact": "9" * CONTACT_LEN},
        {"name": "N", "address": "", "aadhar": "1" * AADHAAR_LEN, "contact": "9" * CONTACT_LEN},
        {"name": "N", "address": "A", "aadhar": "x" * AADHAAR_LEN, "contact": "9" * CONTACT_LEN},
        {"name": "N", "address": "A", "aadhar": "1" * (AADHAAR_LEN-1), "contact": "9" * CONTACT_LEN},
        {"name": "N", "address": "A", "aadhar": "1" * AADHAAR_LEN, "contact": "9" * (CONTACT_LEN-1)},
    ]
)
def test_customer_invalid(kwargs):
    with pytest.raises(ValueError):
        Customer(**kwargs)

# Account lifecycle (Bank)

def test_create_and_read_balance(bank_tmp: Bank):
    acc = open_account(bank_tmp)
    bal = bank_tmp.get_balance(acc, "1234")
    assert isinstance(bal, float) and math.isclose(bal, 1000.0)


def test_invalid_account_or_pin_format_raises(bank_tmp: Bank):
    acc = open_account(bank_tmp)
    # Account must be digits of min length
    with pytest.raises(ValueError):
        bank_tmp.get_balance("abc", "1234")
    with pytest.raises(ValueError):
        bank_tmp.get_balance("12#4", "1234")
    # PIN length invalid
    with pytest.raises(ValueError):
        bank_tmp.get_balance(acc, "12a4")


def test_deposit_and_withdraw_success(bank_tmp: Bank):
    acc = open_account(bank_tmp)
    new_bal = bank_tmp.deposit(acc, "1234", 500)
    assert math.isclose(new_bal, 1500.0)
    w = bank_tmp.withdraw(acc, "1234", 300)
    assert math.isclose(w, 1200.0)


def test_withdraw_insufficient_funds(bank_tmp: Bank):
    acc = open_account(bank_tmp, initial=100.0)
    msg = bank_tmp.withdraw(acc, "1234", 200.0)
    assert isinstance(msg, str) and "Insufficient" in msg


@pytest.mark.parametrize("amt", ["abc", "12#", "#", None])
def test_amount_bad_formats_raise(bank_tmp: Bank, amt):
    acc = open_account(bank_tmp)
    with pytest.raises(ValueError):
        bank_tmp.deposit(acc, "1234", amt)


def test_zero_and_negative_amounts(bank_tmp: Bank):
    acc = open_account(bank_tmp)
    # Zero not allowed for deposit/withdraw per business rule (allow_zero=False)
    with pytest.raises(ValueError):
        bank_tmp.deposit(acc, "1234", 0)
    with pytest.raises(ValueError):
        bank_tmp.withdraw(acc, "1234", 0)
    # Negative not allowed
    with pytest.raises(ValueError):
        bank_tmp.deposit(acc, "1234", -100)

"""
def test_close_account_and_post_ops(bank_tmp: Bank):
    acc = open_account(bank_tmp)
    assert bank_tmp.close_account(acc, "1234") == "Closed"
    # After closing, deposit/withdraw/balance should be blocked politely
    assert bank_tmp.deposit(acc, "1234", 10.0) == "Account not active"
    assert bank_tmp.withdraw(acc, "1234", 10.0) == "Account not active"
    # get_balance returns string message on invalid state or wrong pin; here account exists but we expect not active to be handled via state in get_balance
    gb = bank_tmp.get_balance(acc, "1234")
    assert isinstance(gb, str) and ("not active" in gb.lower() or "closed" in gb.lower())


def test_account_summary_and_active_list(bank_tmp: Bank):
    a1 = open_account(bank_tmp, initial=100)
    a2 = open_account(bank_tmp, initial=200)
    open_account(bank_tmp, initial=0)
    bank_tmp.close_account(a2, "1234")
    actives = bank_tmp.list_active_accounts()
    assert a1 in actives and a2 not in actives
    summary = bank_tmp.account_summary()
    assert isinstance(summary, dict) and a1 in summary and a2 not in summary

# Lockout behavior

def test_lockout_after_5_wrong_pins(bank_tmp: Bank):
    acc = open_account(bank_tmp)

    # 1st to 4th wrong attempt: expect 'Invalid PIN' and, on 4th, warning text
    for i in range(1, 5):
        res = bank_tmp.get_balance(acc, "0000")
        assert isinstance(res, str) and "Invalid PIN" in res
        if i == 4:
            assert "Warning" in res or "attempt left" in res

    # 5th wrong attempt triggers lock
    res5 = bank_tmp.get_balance(acc, "0000")
    assert isinstance(res5, str) and "locked" in res5.lower()

    # After lock, even correct PIN should return locked
    res_correct_after_lock = bank_tmp.get_balance(acc, "1234")
    assert isinstance(res_correct_after_lock, str) and "locked" in res_correct_after_lock.lower()


def test_failed_attempts_reset_on_success(bank_tmp: Bank):
    acc = open_account(bank_tmp)
    # Wrong once
    r1 = bank_tmp.get_balance(acc, "0000")
    assert isinstance(r1, str) and "Invalid PIN" in r1
    # Right now should reset attempts to 0
    ok = bank_tmp.get_balance(acc, "1234")
    assert isinstance(ok, float)
    # Wrong again should be 'first' wrong after reset, not locked
    r2 = bank_tmp.get_balance(acc, "0000")
    assert isinstance(r2, str) and "Invalid PIN" in r2 and "locked" not in r2.lower()
"""
# Create account input categories


@pytest.mark.parametrize(
    "name,address,aadhar,contact,pin,atype,expect_error",
    [
        ("Num3r1cN4m3", "Addr1", "1" * AADHAAR_LEN, "9" * CONTACT_LEN, "1234", "SAVINGS", False),  # alphanumerics ok for name
        ("#@!$", "Addr", "1" * AADHAAR_LEN, "9" * CONTACT_LEN, "1234", "SAVINGS", False),            # specials in name allowed (business decision)
        ("Alice", "A#@!$", "1" * AADHAAR_LEN, "9" * CONTACT_LEN, "1234", "CURRENT", False),          # specials in address allowed
        ("Alice", "Addr", "12a456789012", "9" * CONTACT_LEN, "1234", "SAVINGS", True),               # bad aadhar
        ("Alice", "Addr", "1" * AADHAAR_LEN, "98a6543210", "1234", "SAVINGS", True),               # bad contact
        ("Alice", "Addr", "1" * AADHAAR_LEN, "9" * CONTACT_LEN, "12#4", "SAVINGS", True),           # bad pin
        ("Alice", "Addr", "1" * AADHAAR_LEN, "9" * CONTACT_LEN, "1234", "UNKNOWN", True),           # bad account type
    ]
)
def test_create_account_various_inputs(bank_tmp: Bank, name, address, aadhar, contact, pin, atype, expect_error):
    if expect_error:
        with pytest.raises(ValueError):
            open_account(bank_tmp, name=name, address=address, aadhar=aadhar, contact=contact, pin=pin, atype=atype)
    else:
        acc = open_account(bank_tmp, name=name, address=address, aadhar=aadhar, contact=contact, pin=pin, atype=atype)
        assert isinstance(acc, int)

# Non-existent account

def test_non_existent_account_messages(bank_tmp: Bank):
    # When account is not in file, API should return friendly string, not crash
    # Note: format validation is done first, so provide valid-looking numbers
    fake_acc = 9999
    res = bank_tmp.deposit(fake_acc, "1234", 10.0)
    assert res == "Account not found"
    res2 = bank_tmp.withdraw(fake_acc, "1234", 10.0)
    assert res2 == "Account not found"
    res3 = bank_tmp.get_balance(fake_acc, "1234")
    assert res3 == "Account not found"
