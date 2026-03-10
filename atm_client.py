# atm_client.py
import socket

HOST, PORT = "127.0.0.1", 5000

PIN_LEN = 4
ACC_MIN_LEN = 4

def is_digits(value: str, length: int = None, min_len: int = None) -> bool:
    if value is None:
        return False
    v = str(value).strip()
    if not v.isdigit():
        return False
    if length is not None and len(v) != length:
        return False
    if min_len is not None and len(v) < min_len:
        return False
    return True

def read_account_no(prompt="Enter Account Number: "):
    while True:
        acc = input(prompt).strip()
        if not is_digits(acc, min_len=ACC_MIN_LEN):
            print(f"Error: Account number must be digits (≥{ACC_MIN_LEN} digits). Try again.")
            continue
        return acc

def read_pin(prompt="Enter PIN (4 digits): "):
    while True:
        pin = input(prompt).strip()
        if not is_digits(pin, length=PIN_LEN):
            print("Error: PIN must be exactly 4 digits. Try again.")
            continue
        return pin

def read_amount(prompt="Enter Amount: ", allow_zero=False):
    while True:
        txt = input(prompt).strip()
        try:
            amt = float(txt)
        except Exception:
            print("Error: Amount must be a number. Try again.")
            continue
        if allow_zero:
            if amt < 0:
                print("Error: Amount must be ≥ 0. Try again.")
                continue
        else:
            if amt <= 0:
                print("Error: Amount must be > 0. Try again.")
                continue
        return amt

def send_req(msg: str) -> str:
    s = socket.socket()
    try:
        s.connect((HOST, PORT))
        s.send(msg.encode())
        resp = s.recv(4096).decode()
        return resp
    except Exception as e:
        return f"Error: {e}"
    finally:
        try:
            s.close()
        except Exception:
            pass

def atm_session():
    print("\nWelcome to the ATM")
    acc = read_account_no()
    pin = read_pin()

    # Verify login silently using BALANCE
    res = send_req(f"BALANCE|{acc}|{pin}")
    if res.startswith("Error:") or res in ("Account not found", "Invalid PIN"):
        print(f"Login failed: {res}")
        return

    while True:
        print("\nATM MENU")
        print("1. Withdraw")
        print("2. Deposit")
        print("3. Check Balance")
        print("4. Exit")
        ch = input("Choose: ").strip()

        if ch == "1":
            amt = read_amount("Withdraw Amount: ", allow_zero=False)
            print(send_req(f"WITHDRAW|{acc}|{pin}|{amt}"))

        elif ch == "2":
            amt = read_amount("Deposit Amount: ", allow_zero=False)
            print(send_req(f"DEPOSIT|{acc}|{amt}"))

        elif ch == "3":
            print(send_req(f"BALANCE|{acc}|{pin}"))

        elif ch == "4":
            print("Goodbye!")
            break

        else:
            print("Invalid choice! Please select 1-4.")

def main():
    while True:
        atm_session()
        again = input("\nStart another session? (y/n): ").strip().lower()
        if again != "y":
            break

if __name__ == "__main__":
    main()