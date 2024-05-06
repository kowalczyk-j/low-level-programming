"""
Nazwa projektu: System konwersji TCP/UDP - “SensNet”
Autorzy: Kinga Świderek
Data utworzenia: 14.01.2024 r.
"""

import unittest
from gateway.gateway import SensorGateway
from user.user import User
from sensor.sensor import Sensor
from gateway.logbook import LogBook


logbook = LogBook(disable_console=True)
gateway = SensorGateway(8080, 8082, logbook)
gateway.start()


class TestUser(unittest.TestCase):
    def test_connect_with_ipv4(self):
        gateway.add_authorize_user("::ffff:127.0.0.1")
        with self.assertLogs(level='INFO') as cm:
            User("localhost", 8082)
        self.assertIn("INFO:gateway.logbook:Connection successfully authorised"
                      " from user ::ffff:127.0.0.1",
                      cm.output)

    def test_connect_with_ipv6(self):
        gateway.add_authorize_user("::1")
        with self.assertLogs(level='INFO') as cm:
            User("localhost", 8082, ipv6=True)
        self.assertIn("INFO:gateway.logbook:Connection successfully authorised"
                      " from user ::1",
                      cm.output)

    def test_ask_sensor(self):
        gateway.add_authorize_user("::ffff:127.0.0.1")
        user = User("localhost", 8082)
        with self.assertLogs(level="INFO") as cm:
            response = user.ask_sensor("1")
        self.assertIn("INFO:gateway.logbook:Searching for data of sensor:"
                      " 1...\n",
                      cm.output)
        self.assertIsInstance(response, list)

    def test_register_authorized(self):
        gateway.add_authorize_user("::ffff:127.0.0.1")
        user = User("localhost", 8082)
        with self.assertLogs(level="INFO") as cm:
            response = user.register()
        self.assertIn("INFO:gateway.logbook:Connection successfully authorised"
                      " from user ::ffff:127.0.0.1", cm.output)
        self.assertTrue(response)

    def test_register_unauthorized(self):
        gateway.revoke_user("::ffff:127.0.0.1")
        with self.assertLogs(level="INFO") as cm:
            # register in constructor - connection closed after attempt
            user = User("localhost", 8082)
        self.assertIn("WARNING:gateway.logbook:Attempted unauthorised"
                      " connection from user ::ffff:127.0.0.1", cm.output)
        with self.assertRaises(OSError):
            user.ask_sensor("1")

    def test_logout_authorized(self):
        gateway.add_authorize_user("::ffff:127.0.0.1")
        user = User("localhost", 8082)
        with self.assertLogs(level='INFO') as cm:
            user.logout()
        self.assertIn("INFO:gateway.logbook:Loging out user"
                      " ::ffff:127.0.0.1...",
                      cm.output)


class TestSensor(unittest.TestCase):
    def test_sensor_register_authorized(self):
        gateway.add_authorize_device("127.0.0.1")
        sensor = Sensor("localhost", 8080, 10)
        with self.assertLogs(level="INFO") as cm:
            sensor.register()
        self.assertIn("INFO:gateway.logbook:Connection successfully authorised"
                      " from sensor 127.0.0.1", cm.output)

    def test_sensor_register_unauthorized(self):
        gateway.revoke_device("127.0.0.1")
        sensor = Sensor("localhost", 8080, 10)
        with self.assertLogs(level="INFO") as cm:
            sensor.register()
        self.assertIn("WARNING:gateway.logbook:Attempted unauthorised"
                      " connection from sensor 127.0.0.1",
                      cm.output)

    def test_sensor_send_data_authorized(self):
        gateway.add_authorize_device("127.0.0.1")
        sensor = Sensor("localhost", 8080, 10)
        with self.assertLogs(level="INFO") as cm:
            sensor.message_data()
        self.assertIn("Received sensor data:", " ".join(cm.output))

    def test_sensor_send_data_unauthorized(self):
        gateway.revoke_device("127.0.0.1")
        sensor = Sensor("localhost", 8080, 10)
        with self.assertLogs(level="INFO") as cm:
            sensor.message_data()
        self.assertIn("WARNING:gateway.logbook:Attempted unauthorised"
                      " connection from sensor 127.0.0.1",
                      cm.output)

    def test_sensor_logout_authorized(self):
        gateway.add_authorize_device("127.0.0.1")
        sensor = Sensor("localhost", 8080, 10)
        with self.assertLogs(level="INFO") as cm:
            sensor.logout()
        self.assertIn("INFO:gateway.logbook:Logging out 127.0.0.1...",
                      cm.output)

    def test_sensor_logout_unauthorized(self):
        gateway.revoke_device("127.0.0.1")
        sensor = Sensor("localhost", 8080, 10)
        with self.assertLogs(level="INFO") as cm:
            sensor.logout()
        self.assertIn("WARNING:gateway.logbook:Attempted unauthorised"
                      " connection from sensor 127.0.0.1",
                      cm.output)


if __name__ == "__main__":
    unittest.main()
