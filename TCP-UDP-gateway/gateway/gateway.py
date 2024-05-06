"""
Nazwa projektu: System konwersji TCP/UDP - “SensNet”
Autorzy: Marcin Kowalczyk, Jakub Kowalczyk
Wsparcie: Kinga Świderek, Magdalena Dudek
Data utworzenia: 02.01.2024 r.
"""
from cryptography.fernet import Fernet
from threading import Lock
from gateway.logbook import LogBook
import socket
import threading
import json
import os
import ipaddress

SENSORS_NETWORK = ipaddress.IPv4Network("127.0.0.0/24")


class SensorGateway:
    def __init__(self, sensor_port, user_port, logger):
        self.sensor_data = {}
        self.sensor_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sensor_socket.bind(('localhost', sensor_port))
        self.user_socket = socket.create_server(
            ("", user_port), family=socket.AF_INET6, dualstack_ipv6=True)
        self.user_socket.listen()
        self.trusted_devices = set()
        self.trusted_users = set()
        self.active_sensors = {} #handling state of connections 
        self.active_users = {} 
        self.lock = Lock()
        self.encryption_key = "" # Read from local file
        self.MAX_SENSORS = 1024
        self.MAX_USERS = 256
        self.logger = logger

    def start(self):
        self.load_fernet_key()
        self.load_trusted_addresses()
        threading.Thread(target=self.handle_sensor_data).start()
        threading.Thread(target=self.handle_user_requests).start()
        self.logger.info("Gateway started")

    def handle_sensor_data(self):
        while True:
            self.logger.info("Waiting for sensor data...")
            data, addr = self.sensor_socket.recvfrom(1024)
            if self.authorize_device(addr[0]):
                try:
                    sensor_info = json.loads(data.decode())
                    action = sensor_info['action']
                    if action == 'data':
                        packet_id = sensor_info["packet_id"]

                        if(addr[0] not in self.active_sensors.keys()):
                            self.active_sensors[addr[0]] = packet_id
                            self.logger.info(f"New active sensor: {addr[0]}")
                            self.sensor_data[addr[0]] = sensor_info['data']
                            self.active_sensors[addr[0]] = packet_id
                            self.logger.info(f"Received sensor data: {self.sensor_data} : packet id = {packet_id}")
                            self.save_data_to_file()
                        elif(packet_id == self.active_sensors[addr[0]]):
                            self.logger.info(f"[OUTDATED] Data already recived. Packet id: {packet_id}")
                        else:
                            self.sensor_data[addr[0]] = sensor_info['data']
                            self.active_sensors[addr[0]] = packet_id
                            self.logger.info(f"Received sensor data: {self.sensor_data} : packet id = {packet_id}")
                            self.save_data_to_file()

                        response = self._create_response(200, json_data={"packet_id": packet_id})

                    elif action == 'logout':
                        ip_address = sensor_info.get('ip_address')
                        self.logger.info(f"Logging out {ip_address}...")
                        #logger.debug(f"Trusted devices before logout: {self.trusted_devices}")
                        self.revoke_device(ip_address)
                        #logger.debug(f"Trusted devices after logout: {self.trusted_devices}")
                        response = self._create_response(200, json_data={
                            "data": 'Pomyślnie wylogowano urządzenie'
                        })

                    else:
                        # Send error response back to the sensor
                        response = self._create_response(400)
                        self.logger.error(f"Received invalid action from {addr[0]}: {action}")

                except json.JSONDecodeError:
                    response = self._create_response(400)
                    self.logger.error(f"Received invalid JSON format from {addr[0]}")
            else:
                response = self._create_response(401)

            self.sensor_socket.sendto(response.encode('utf-8'), addr)

    def handle_user_requests(self):
        while True:
            self.logger.info("Waiting for connection from users...")
            conn, addr = self.user_socket.accept()
            if self.authorize_user(addr[0]):
                threading.Thread(target=self.handle_user_connection, args=(conn, addr)).start()
                #self.handle_user_connection(conn, addr)
            else:
                conn.recv(1024)
                response = self._create_response(401)
                conn.sendall(response.encode('utf-8'))
                self.logger.info("Closing connection...\n")
                conn.close()

    def handle_user_connection(self, conn, addr):
        user_ipaddr = addr[0]
        try:
            while True:
                data = conn.recv(1024)
                if not data:
                    self.logger.error(f"Connection with {user_ipaddr} lost")
                    break
                request = json.loads(data.decode())
                action = request.get('action')
                self.logger.debug(f"Received action: {action} from {user_ipaddr}")
                if action == 'ask':
                    sensor_id = request.get('sensor_id')
                    self.logger.info(f"Searching for data of sensor: {sensor_id}...\n")
                    try:
                        sensor_data = self.retrive_sensor_data(sensor_id)
                        response = self._create_response(
                            200, json_data={"data": sensor_data})
                        self.logger.info(f"Sending data to {user_ipaddr}: {sensor_data}")
                    except KeyError:
                        self.logger.error(f"Sensor {sensor_id} not found")
                        response = self._create_response(404)

                elif action == 'register': #add_authorize_user???
                    if self.authorize_user(user_ipaddr):
                        response = self._create_response(201)
                    else:
                        response = self._create_response(401)

                elif action == 'logout':
                    self.logger.info(f"Loging out user {user_ipaddr}...")
                    self.revoke_user(user_ipaddr)
                    response = self._create_response(202)
                    conn.sendall(response.encode())
                    self.logger.info(f"Closing connection with {user_ipaddr}.\n")
                    conn.close()
                    break
                else:
                    response = self._create_response(400)
                    self.logger.error(f"Received invalid action from {user_ipaddr}: {action}")

                conn.sendall(response.encode())

        except json.JSONDecodeError:
            self.logger.error(f"Received invalid JSON format from {user_ipaddr}")
            response = self._create_response(400)  # Handle invalid JSON format

        finally:
            self.logger.info(f"Closing connection with {user_ipaddr}.\n")
            conn.close()

    # WALIDACJA

    def retrive_sensor_data(self, sensor_id):
        self.load_data_from_file()
        sensor_data = ''
        sensor_ip = sensor_id
        if sensor_id.isdigit():
            sensor_id = int(sensor_id)
            if sensor_id <= int(SENSORS_NETWORK.hostmask):
                sensor_ip = str(SENSORS_NETWORK.network_address + sensor_id)

        sensor_data = self.sensor_data[sensor_ip]

        return sensor_data
    
    def _create_response(self, status_code, object=None, json_data=None):
        response = {}
        response["status_code"] = status_code
        if json_data is not None:
            response.update(json_data)
        return json.dumps(response)
    
    # AUTORYZACJA

    def authorize_user(self, user_address):
        if user_address in self.trusted_users:
            self.logger.info(f"Connection successfully authorised from user {user_address}")
            return True
        else:
            self.logger.warning(f"Attempted unauthorised connection from user {user_address}")
            return False

    def add_authorize_user(self, user_address):
        if len(self.trusted_users) < self.MAX_USERS:
            self.trusted_users.add(user_address)
            self.save_trusted_users()
        else:
            self.logger.error(f"Cannot add user {user_address}: too many authorized")

    def authorize_device(self, device_address):
        if device_address in self.trusted_devices:
            self.logger.info(f"Connection successfully authorised from sensor {device_address}")
            return True
        else:
            self.logger.warning(f"Attempted unauthorised connection from sensor {device_address}")
            return False

    def add_authorize_device(self, device_address):
        if len(self.trusted_devices) < self.MAX_SENSORS:
            self.trusted_devices.add(device_address)
            self.save_trusted_devices()
            self.logger.info(f"Added sensor {device_address} to trusted devices")
        else:
            self.logger.error(f"Cannot add sensor {device_address}: too many authorized")

    def revoke_device(self, ip_address):
        self.trusted_devices.discard(ip_address)
        self.save_trusted_devices()
        self.logger.info(f"Sensor {ip_address} revoked from trusted devices")

    def revoke_user(self, ip_address):
        self.trusted_users.discard(ip_address)
        self.save_trusted_users()
        self.logger.info(f"User {ip_address} revoked from trusted devices")

    def save_trusted_devices(self, filename='trusted_devices.json'):
        encrypted_devices = [self.encryption_key.encrypt(device.encode()).decode() for device in self.trusted_devices]
        with self.lock:
            with open(filename, 'w') as f:
                json.dump(encrypted_devices, f)

    def save_trusted_users(self, filename='trusted_users.json'):
        encrypted_users = [self.encryption_key.encrypt(user.encode()).decode() for user in self.trusted_users]
        with self.lock:
            with open(filename, 'w') as f:
                json.dump(encrypted_users, f)

    def load_trusted_addresses(self, filename_dev='trusted_devices.json', filename_user='trusted_users.json'):
        if os.path.exists(filename_dev):
            with self.lock:
                with open(filename_dev, 'r') as f:
                    encrypted_devices = json.load(f)
                    self.trusted_devices = set(self.encryption_key.decrypt(device.encode()).decode() for device in encrypted_devices)
        if os.path.exists(filename_user):
            with self.lock:
                with open(filename_user, 'r') as f:
                    encrypted_users = json.load(f)
                    self.trusted_users = set(self.encryption_key.decrypt(user.encode()).decode() for user in encrypted_users)

    def load_fernet_key(self):
        with open('gateway/secret.key', 'rb') as key_file:
            self.encryption_key = Fernet(key_file.read())

    # ZARZĄDCA PAMIĘCI

    def save_data_to_file(self, filename='sensors.json'):
        with self.lock:
            with open(filename, 'w') as f:
                json.dump(self.sensor_data, f)

    def load_data_from_file(self, filename='sensors.json'):
        if os.path.exists(filename):
            with self.lock:
                with open(filename, 'r') as f:
                    self.sensor_data = json.load(f)


if __name__ == '__main__':
    logger = LogBook()
    gateway = SensorGateway(sensor_port=8080, user_port=8082, logger=logger)
    # gateway.add_authorize_user("::ffff:127.0.0.1")
    # gateway.add_authorize_user("::1")
    # gateway.add_authorize_device("127.0.0.1")
    # gateway.add_authorize_device("0.0.0.0")
    gateway.start()
    # gateway.save_trusted_addresses()
