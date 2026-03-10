# bank_server.py
import socket
import threading

from bank import (
    Bank, Customer, PIN_LEN, AADHAAR_LEN, CONTACT_LEN, ACC_MIN_LEN,
    is_digits, 
)

HOST = "127.0.0.1"
PORT = 5000

bank = Bank()

# --------------------------
# Server: ATM Protocol
# --------------------------
# Commands:
# CREATE|name|address|aadhar|contact|pin|initial|type
# DEPOSIT|acc_no|amount
# WITHDRAW|acc_no|pin|amount
# BALANCE|acc_no|pin
# CLOSE|acc_no|pin
# ACTIVE_LIST
# SUMMARY

def handle_client(conn, addr):
    try:
        data = conn.recv(4096).decode().strip()
        parts = data.split("|") if data else []
        cmd = parts[0].upper() if parts else ""

        if cmd == "CREATE":
            if len(parts) != 8:
                resp = "Error: CREATE requires 7 parameters."
            else:
                _, name, address, aadhar, contact, pin, initial, atype = parts
                acc = bank.create_account(Customer(name, address, aadhar, contact),
                                          pin, float(initial), atype)
                resp = f"Account Created: {acc}"

        elif cmd == "DEPOSIT":
            if len(parts) != 3:
                resp = "Error: DEPOSIT requires acc_no and amount."
            else:
                _, acc_no, amount = parts
                if not is_digits(acc_no, min_len=ACC_MIN_LEN):
                    resp = "Error: Invalid Account Number."
                else:
                    newb = bank.deposit(int(acc_no), float(amount))
                    resp = f"New Balance: {newb}"

        elif cmd == "WITHDRAW":
            if len(parts) != 4:
                resp = "Error: WITHDRAW requires acc_no, pin, amount."
            else:
                _, acc_no, pin, amount = parts
                if not is_digits(acc_no, min_len=ACC_MIN_LEN) or not is_digits(pin, length=PIN_LEN):
                    resp = "Error: Invalid Account or PIN."
                else:
                    res = bank.withdraw(int(acc_no), pin, float(amount))
                    resp = str(res)

        elif cmd == "BALANCE":
            if len(parts) != 3:
                resp = "Error: BALANCE requires acc_no and pin."
            else:
                _, acc_no, pin = parts
                if not is_digits(acc_no, min_len=ACC_MIN_LEN) or not is_digits(pin, length=PIN_LEN):
                    resp = "Error: Invalid Account or PIN."
                else:
                    res = bank.get_balance(int(acc_no), pin)
                    resp = str(res)

        elif cmd == "CLOSE":
            if len(parts) != 3:
                resp = "Error: CLOSE requires acc_no and pin."
            else:
                _, acc_no, pin = parts
                if not is_digits(acc_no, min_len=ACC_MIN_LEN) or not is_digits(pin, length=PIN_LEN):
                    resp = "Error: Invalid Account or PIN."
                else:
                    res = bank.close_account(int(acc_no), pin)
                    resp = str(res)

        elif cmd == "ACTIVE_LIST":
            resp = ",".join(map(str, bank.list_active_accounts()))

        elif cmd == "SUMMARY":
            d = bank.account_summary()
            parts = [f"{k}:{v}" for k, v in d.items()]
            resp = ";".join(parts)

        else:
            resp = "Error: Unknown command"

        conn.send(resp.encode())

    except Exception as e:
        try:
            conn.send(f"Error: {e}".encode())
        except Exception:
            pass
    finally:
        conn.close()

def start_server():
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen()
    print(f"[Server] Bank Server started on {HOST}:{PORT}")
    while True:
        conn, addr = s.accept()
        t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
        t.start()

# --------------------------
# Bank Operator Console (CLI)
# --------------------------
def input_digits(prompt, *, exact=None, min_len=None, field="Value"):
    while True:
        v = input(prompt).strip()
        if is_digits(v, length=exact, min_len=min_len):
            return v
        if exact:
            print(f"Error: {field} must be exactly {exact} digits. Try again.")
        else:
            print(f"Error: {field} must be digits (min length {min_len}). Try again.")

def input_amount(prompt, allow_zero=True):
    while True:
        s = input(prompt).strip()
        try:
            amt = float(s)
        except Exception:
            print("Error: Amount must be a number. Try again.")
            continue
        if not allow_zero and amt <= 0:
            print("Error: Amount must be > 0. Try again.")
            continue
        if allow_zero and amt < 0:
            print("Error: Amount must be ≥ 0. Try again.")
            continue
        return amt

def bank_console():
    print("\n=== Bank Operator Console ===")
    while True:
        print("\nBANK MENU")
        print("1. Create Account")
        print("2. Deposit")
        print("3. Withdraw")
        print("4. Close Account")
        print("5. Exit")
        ch = input("Choose: ").strip()

        try:
            if ch == "1":
                name = input("Name: ").strip()
                address = input("Address: ").strip()
                aadhar = input_digits("Aadhaar (12 digits): ", exact=AADHAAR_LEN, field="Aadhaar")
                contact = input_digits("Contact (10 digits): ", exact=CONTACT_LEN, field="Contact")
                pin = input_digits("Set PIN (4 digits): ", exact=PIN_LEN, field="PIN")
                initial = input_amount("Initial deposit (default 0): ", allow_zero=True)
                atype = input("Account Type (SAVINGS/CURRENT) [SAVINGS]: ").strip().upper() or "SAVINGS"

                acc = bank.create_account(Customer(name, address, aadhar, contact), pin, initial, atype)
                print(f"✔ Account Created: {acc}")

            elif ch == "2":
                acc_no = input_digits("Account No: ", min_len=ACC_MIN_LEN, field="Account No")
                amount = input_amount("Deposit Amount: ", allow_zero=False)
                newb = bank.deposit(int(acc_no), amount)
                print(f"✔ New Balance: {newb}")

            elif ch == "3":
                acc_no = input_digits("Account No: ", min_len=ACC_MIN_LEN, field="Account No")
                pin = input_digits("PIN (4 digits): ", exact=PIN_LEN, field="PIN")
                amount = input_amount("Withdraw Amount: ", allow_zero=False)
                res = bank.withdraw(int(acc_no), pin, amount)
                print(f"✔ {res}")

            elif ch == "4":
                acc_no = input_digits("Account No: ", min_len=ACC_MIN_LEN, field="Account No")
                pin = input_digits("PIN (4 digits): ", exact=PIN_LEN, field="PIN")
                res = bank.close_account(int(acc_no), pin)
                print(f"✔ {res}")

            elif ch == "5":
                print("Exiting Bank Console. Server continues to run...")
                break

            else:
                print("Invalid choice! Please select 1-5.")

        except Exception as e:
            print(f"Error: {e}")

def main():
    # Start server in background
    server_thr = threading.Thread(target=start_server, daemon=True)
    server_thr.start()

    # Run bank operator console
    bank_console()

    print("Press Ctrl+C to stop the server.")
    server_thr.join()

if __name__ == "__main__":
    main()