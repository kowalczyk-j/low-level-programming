"""
Nazwa projektu: System konwersji TCP/UDP - “SensNet”
Autor: Kinga Świderek
Data utworzenia: 01.01.2024 r.
"""
import json
import socket
import sys

MAXLINE = 512


class User:
    def __init__(self, server_ip, server_port, ipv6=False):
        self.server_ip = server_ip
        self.server_port = server_port
        sock_type = socket.AF_INET6 if ipv6 else socket.AF_INET
        self.sock = socket.socket(sock_type, socket.SOCK_STREAM)
        print("Trying to connect with server...")
        self.sock.connect((self.server_ip, self.server_port))
        print("Connected to gate.")
        print("Trying to authorize...")
        if self.register():
            print("Succesfull authorized.")
        else:
            print("Unable to communicate with server.")
            self.sock.close()

    def __del__(self):
        self.sock.close()

    def ask_sensor(self, sensor_id):
        message = self._create_message("ask", sensor_id)
        response = self._send_message(message)
        return self._check_status(response)

    def register(self):
        message = self._create_message("register")
        response_str = self._send_message(message)
        response = json.loads(response_str)
        try:
            if int(response["status_code"]) == 201:
                return True
            else:
                print(self._check_status(response_str))
                return False
        except KeyError:
            print("Error response:", response)
            return False

    def logout(self):
        message = self._create_message("logout")
        response = self._send_message(message)
        return self._check_status(response)

    def _create_message(self, action, *args):
        message = {"action": action}
        if action == "ask":
            message["sensor_id"] = args[0]
        return json.dumps(message)

    def _send_message(self, message):
        self.sock.sendall(message.encode("utf-8"))
        response = self.sock.recv(MAXLINE).decode("utf-8")
        return response

    def _check_status(self, response):
        try:
            response = json.loads(response)
        except json.JSONDecodeError:
            return "Response error"
        else:
            status_code = response["status_code"]
            if status_code == 200:
                return response["data"]
            elif status_code == 201:
                return "Register successful."
            elif status_code == 202:
                return "Logout succesful."
            elif status_code == 401:
                return "Unauthorized connection."
            elif status_code == 404:
                return "No senor with given ID."
            return "Server error."


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Improper arguments, should be: server ip, server port")
        exit(1)

    user = User(sys.argv[1], int(sys.argv[2]))

    while True:
        print("\nOptions:")
        print("1. Logout user")
        print("2. Ask for sensor data")
        print("3. Quit")
        choice = input("Choose an option (1-3): ")

        if choice == '1':     # LOGOUT
            message = user.logout()
            print('waiting for confirmation...')
            print(message)
            print('Exiting...')
            break

        elif choice == '2':     # ASK FOR COLLECTED DATA
            sensor_id = input("Choose sensor id: ")
            message = user.ask_sensor(sensor_id)
            print(f"Data collected: {message}")

        elif choice == '3':
            print("Quitting the program.")
            break

        else:
            print("Invalid choice. Please select a valid option.")
