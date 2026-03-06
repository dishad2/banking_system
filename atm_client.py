# atm_client.py
import socket

HOST, PORT = "127.0.0.1", 5000

def send_req(msg: str) -> str:
    s = socket.socket()
    s.connect((HOST, PORT))
    s.send(msg.encode())
    resp = s.recv(1024).decode()
    s.close()
    return resp

def main():
    while True:
        print("\nATM MENU")
        print("1. Create Account")
        print("2. Deposit")
        print("3. Withdraw")
        print("4. Check Balance")
        print("5. Close Account")
        print("6. List Active Accounts")
        print("7. Summary (acc:bal)")
        print("8. Exit")
        ch = input("Choose: ").strip()

        if ch == "1":
            name = input("Name: ")
            aadhar = input("Aadhar: ")
            contact = input("Contact: ")
            pin = input("Set PIN: ")
            initial = input("Initial deposit (default 0): ") or "0"
            print(send_req(f"CREATE|{name}|{aadhar}|{contact}|{pin}|{initial}"))

        elif ch == "2":
            acc = input("Account No: ")
            amt = input("Amount: ")
            print(send_req(f"DEPOSIT|{acc}|{amt}"))

        elif ch == "3":
            acc = input("Account No: ")
            pin = input("PIN: ")
            amt = input("Amount: ")
            print(send_req(f"WITHDRAW|{acc}|{pin}|{amt}"))

        elif ch == "4":
            acc = input("Account No: ")
            pin = input("PIN: ")
            print(send_req(f"BALANCE|{acc}|{pin}"))

        elif ch == "5":
            acc = input("Account No: ")
            pin = input("PIN: ")
            print(send_req(f"CLOSE|{acc}|{pin}"))

        elif ch == "6":
            print("Active accounts:", send_req("ACTIVE_LIST"))

        elif ch == "7":
            print("Summary:", send_req("SUMMARY"))

        elif ch == "8":
            break
        else:
            print("Invalid choice!")

if __name__ == "__main__":
    main()