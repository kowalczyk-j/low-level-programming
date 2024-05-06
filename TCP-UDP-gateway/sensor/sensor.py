"""
Nazwa projektu: System konwersji TCP/UDP - “SensNet”
Autor: Magdalena Dudek
Data utworzenia: 01.01.2024 r.
"""

from datetime import datetime
import select 
import socket
import sys
import time
import random
import json


MAXLINE = 512  # Maximum message length that the client can receive
TIMEOUT = 1 #timeout in sec for retransmission
RESENDING_TRIES = 5 #number of tries to resend packet

# SENSOR_IP_ADDRESS = socket.gethostbyname(socket.gethostname())
SENSOR_IP_ADDRESS = "localhost"

class Sensor:
    def __init__(self, server_ip, server_port, interval):
        self.server_address_port = (server_ip, int(server_port))
        self.sensor_socket = socket.socket(
            family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.sensor_socket.settimeout(TIMEOUT)
        
        # timeout with select
        #self.ready = [True]
        # if(retransmission):
        #     #seting socket in non-blocking mode becase our select
        #     self.sensor_socket.setblocking(0)
        #     self.ready = select.select([self.sensor_socket], [], [], TIMEOUT)

        self.sensor_socket.bind((SENSOR_IP_ADDRESS, 0))
        self.local_address = self.sensor_socket.getsockname()
        print(self.local_address)
        self.interval = interval
        self.packet_id = 0
        self.current_data = None

    def collect_data(self):
        # Przykładowe dane, które mogą być generowane przez sensor
        humidity = random.randint(1, 100)
        timestamp = datetime.now().strftime("%m/%d/%y %H:%M:%S")

        # Struktura danych zgodna z podanym formatem
        data = [
            {
                "humidity": humidity,
                "timestamp": timestamp
            }
        ]
        return data

    def increase_packet_id(self):
        if self.packet_id == 0:
            self.packet_id = 1
        else:
            self.packet_id = 0

    def message_data(self):
        self.current_data = self.collect_data()
        message = {"packet_id": self.packet_id}
        message["action"] = "data"
        message["data"] = self.current_data
        response = False
        i=0
        while(not response):
            i += 1
            try:
                response = self._send_message(json.dumps(message))
                response_json = json.loads(response)
                recived_packet_id =response_json["packet_id"]
                if (recived_packet_id != self.packet_id):
                    print(f"Recived outdated ACK for packet id: {recived_packet_id}")
                    response = False
                    raise TimeoutError
            except TimeoutError:
                print(f"[{i}] Timeout. Resending data.")
                if(i>=RESENDING_TRIES):
                    print("No connection with server.")
                    response = json.dumps({"status_code" : -1})
            except KeyError:
                print("Couldn't read response.")
        self.increase_packet_id()
        return response

    def register(self):
        message = self._create_message("register")
        return self._send_message(message)

    def logout(self):
        message = self._create_message("logout")
        return self._send_message(message)

    def _create_message(self, action):
        message = {"action": action}
        message["ip_address"] = self.local_address[0]
        return json.dumps(message)

    def _send_message(self, message):
        self.sensor_socket.sendto(message.encode(
            "utf-8"), self.server_address_port)
        print("Message sent")
        response = self.sensor_socket.recv(MAXLINE).decode("utf-8")
        return response

    def _check_status(self, response):
        status_code = response["status_code"]
        if status_code == 200:
            return (response["data"] if response.get("data")
                    else "CODE 200: Pomyślnie przesłano dane")
        elif status_code == 401:
            return "CODE 401: Nieautoryzowane połączenie"
        return "Błąd po stronie serwera."

    def close(self):
        self.sensor_socket.close()


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Improper arguments, should be: server ip, server port, interval")
        exit(1)

    time_interval = float(sys.argv[3])
    sensor = Sensor(sys.argv[1], int(sys.argv[2]), time_interval)

    while True:
        print("\nOptions:")
        print("1. Logout sensor")
        print("2. Start sending data")
        print("3. Quit")
        choice = input("Choose an option (1-3): ")

        if choice == '1':     # LOGOUT
            response = sensor.logout()
            print('waiting for confirmation...')
            response = json.loads(response)
            print(response)
            print(sensor._check_status(response))

        elif choice == '2':  # SEND COLLECTED DATA
            status_code = '200'
            while True:
                try:
                    response = sensor.message_data()
                    response = json.loads(response)
                    print("Response: ", response)
                    if response["status_code"] != 200:
                        print(f'\n{sensor._check_status(response)}')
                        break
                    time.sleep(time_interval)
                except KeyboardInterrupt:
                    break

        elif choice == '3':
            print("Quitting the program.")
            break

        else:
            print("Invalid choice. Please select a valid option.")
