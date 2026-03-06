# bank_server.py
import socket
from bank import Bank, Customer

bank = Bank()

def start_server(host="127.0.0.1", port=5000):
    s = socket.socket()
    s.bind((host, port))
    s.listen()
    print(f"Bank Server started on {host}:{port}")

    while True:
        conn, addr = s.accept()
        try:
            data = conn.recv(1024).decode().strip()
            parts = data.split("|")
            cmd = parts[0] if parts else ""

            if cmd == "CREATE":
                # CREATE|name|aadhar|contact|pin|initial
                _, name, aadhar, contact, pin, initial = parts
                acc = bank.create_account(Customer(name, aadhar, contact), pin, float(initial))
                resp = f"Account Created: {acc}"

            elif cmd == "DEPOSIT":
                # DEPOSIT|acc_no|amount
                _, acc_no, amount = parts
                newb = bank.deposit(int(acc_no), float(amount))
                resp = f"New Balance: {newb}"

            elif cmd == "WITHDRAW":
                # WITHDRAW|acc_no|pin|amount
                _, acc_no, pin, amount = parts
                res = bank.withdraw(int(acc_no), pin, float(amount))
                resp = str(res)

            elif cmd == "BALANCE":
                # BALANCE|acc_no|pin
                _, acc_no, pin = parts
                res = bank.get_balance(int(acc_no), pin)
                resp = str(res)

            elif cmd == "CLOSE":
                # CLOSE|acc_no|pin
                _, acc_no, pin = parts
                res = bank.close_account(int(acc_no), pin)
                resp = str(res)

            elif cmd == "ACTIVE_LIST":
                # returns account numbers of active accounts (uses list comprehension)
                resp = ",".join(map(str, bank.list_active_accounts()))

            elif cmd == "SUMMARY":
                # returns "acc:bal;acc:bal;..." (dict comprehension)
                d = bank.account_summary()
                parts = [f"{k}:{v}" for k, v in d.items()]
                resp = ";".join(parts)

            else:
                resp = "Unknown command"

            conn.send(resp.encode())
        except Exception as e:
            conn.send(f"Error: {e}".encode())
        finally:
            conn.close()

if __name__ == "__main__":
    start_server()