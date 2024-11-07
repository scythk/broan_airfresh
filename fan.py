import socket
import struct
import logging

from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.fan import FanEntity, SPEED_OFF, SPEED_LOW, SPEED_MEDIUM, SPEED_HIGH
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

# import custom_components.broan as broan

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

ENTITYID = "fan." + DOMAIN

CONF_HOST = "host"
CONF_PORT = "port"
CONF_ADDRESS = "address"

SPEED_MAPPING = {
    0: SPEED_OFF,
    1: SPEED_LOW,
    2: SPEED_MEDIUM,
    3: SPEED_HIGH
}

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_HOST): cv.string,
                vol.Required(CONF_PORT): cv.positive_int,
                vol.Optional(CONF_ADDRESS, default="00"): cv.string,
            }),
    },
    extra=vol.ALLOW_EXTRA)

def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_devices,
    discovery_info = None
) -> None:
    """Set up the sensor platform."""
    # We only want this platform to be set up via discovery.
    # add_entities([ExampleSensor()])

    dev = []
    _LOGGER.info("setup platform")
    # broan = hass.data["broan"]
    dev.append(BroanFan(hass, config))
    add_devices(dev, True)


class BroanFan(FanEntity):

    def __init__(self, hass, config):
        br = hass.data[DOMAIN]

        self._hass = hass
        self._config = config
        # self.broan = broan
        self._status = None
        self._state = "off"
        self._speed = "03"
        self._direction = None
        self._mode = None
        self._name = "broan_airfresh"
        self._temper = None
        self._humidity = None
        # self.state = None
        self.Host_Id = "02"
        self.Mode = None
        self.M1_speed = None
        self.M2_speed = None
        self.New_Opt = "5a"
        self.End_Flag = "f5"
        self.Strat_Flag = "aa"
        self.Address = "00"
        self.host = br.get(CONF_HOST)
        self.port = br.get(CONF_PORT)
        self.Temper = None
        self.Humidity = None
        self.Error_Code = None

    @property
    def name(self):
        """Return the name of the fan."""
        return self._name

    @property
    def speed(self):
        """Return the current speed."""
        return self._speed

    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        return 'mdi:air-conditioner'

    @property
    def speed_list(self):
        """List of available fan modes."""
        return [SPEED_OFF, SPEED_LOW, SPEED_MEDIUM, SPEED_HIGH]

    @property
    def device_state_attributes(self):
        # if self._direction == DIRECTION_REVERSE:
            # self._mode = "换气"
        # elif self._direction == DIRECTION_FORWARD:
            # self._mode = "排风"
        # self._temper = self.Temper
        # self._humidity = self.Humidity
        self._status = self.Error_Code
        data = {"direction": self._direction, "speed": self._speed, "status": self._status, "mode": self.Mode, "temper": self._temper, "humidity": self._humidity}
        return data

    @property
    def is_on(self):
        """Return true if light is on."""
        _LOGGER.info("is on: " + str(self._state))
        self.search()
        # self._state = "on"
        # self._mode = "排风"
        return self._state not in ["off", None]

    def turn_off(self, **kwargs):
        # self._speed = SPEED_OFF
        self._direction = None
        self._state = "off"
        mode = "00"
        m1_speed = "00"
        m2_speed = "00"

        cmd = self.make_cmd(mode, m1_speed, m2_speed, None)
        response = self.send_cmd(cmd)
        _LOGGER.info("components turn off: " + str(response))

    def turn_on(self, speed: str=None, **kwargs):
        if speed is None:
            real_speed = self._speed
        elif speed == "low":
            real_speed = "01"
        elif speed == "medium":
            real_speed = "01"
        elif speed == "high":
            real_speed = "03"
        elif speed == "off":
            real_speed = "00"
        else:
            real_speed = speed
        _LOGGER.info("turn on speed: " + real_speed)
        self._speed = real_speed
        self._state = "on"
        mode = "01"
        m1_speed = real_speed
        if speed == "medium":
            m2_speed = "03"
        else:
            m2_speed = real_speed
        cmd = self.make_cmd(mode, m1_speed, m2_speed, None)
        response = self.send_cmd(cmd)
        _LOGGER.info("components turn on: " + str(response))

    def set_speed(self, speed: str):
        if speed is None:
            real_speed = self._speed
        elif speed == "low":
            real_speed = "01"
        elif speed == "medium":
            real_speed = "01"
        elif speed == "high":
            real_speed = "03"
        elif speed == "off":
            real_speed = "00"
        else:
            real_speed = speed

        _LOGGER.info("speed: " + real_speed)
        m1_speed = real_speed
        if speed == "medium":
            m2_speed = "03"
        else:
            m2_speed = real_speed
        if self._state == "on":
            mode = "01"
            cmd = self.make_cmd(mode, m1_speed, m2_speed, None)
            response = self.send_cmd(cmd)
            _LOGGER.info("set speed: " + str(response))
        self._speed = real_speed
        return self._speed

    def send_cmd(self, cmd):
        try:
            host = socket.gethostbyname(self.host)
            port = (host, self.port)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(port)
            s.send(cmd)
            _LOGGER.info("send cmd: " + str(cmd))
            message = s.recv(11)
            message = ''.join(['%02x' % b for b in message])
            s.close()
            return message
        except Exception as e:
            _LOGGER.info(e)
            return e

    def make_cmd(self, mode, m1_speed, m2_speed, new_opt):
        if new_opt is None:
            checksum = bytes.fromhex(self.Address + self.Host_Id + mode + m1_speed + m2_speed + self.New_Opt)
            a = checksum[1:]
            b = "%x"%sum(a)
            cmd = bytes.fromhex(self.Strat_Flag + self.Address + self.Host_Id + mode + m1_speed + m2_speed + self.New_Opt + str(b) + self.End_Flag)
        else:
            checksum = bytes.fromhex(self.Address + self.Host_Id + mode + m1_speed + m2_speed + new_opt)
            a = checksum[1:]
            b = "%x"%sum(a)
            cmd = bytes.fromhex(self.Strat_Flag + self.Address + self.Host_Id + mode + m1_speed + m2_speed + new_opt + str(b) + self.End_Flag)
        return cmd

    def search(self):
        mode = "00"

        m1_speed = "00"
        m2_speed = "00"
        new__opt = "a5"

        cmd = self.make_cmd(mode, m1_speed, m2_speed, new__opt)
        response = self.send_cmd(cmd)
        _LOGGER.info("search: " + str(response))
        self.Mode = response[6:8]
        self.M1_speed = response[8:10]
        self.M2_speed = response[10:12]
        temper = response[12:14]
        self._humidity = response[14:16]
        error_code = bin(int(response[16:18], 16))[2:].rjust(8, "0")
        temper = bin(int(temper, 16))[2:].rjust(8, "0")

        if temper.startswith("0", 0, 1):
            self._temper = int(temper, 2)
        else:
            self._temper = -int(temper, 2)

        if self.Mode == "00":  # 模式为关机
            self._state = "off"
        else:
            self._state = "on"

        m1_status = error_code[2:3]
        m2_status = error_code[3:4]
        tem_status = error_code[6:7]
        hum_status = error_code[7:8]
        data = [m1_status, m2_status, tem_status, hum_status]
        e = ""
        for i in range(len(data)):
            if data[i] == "1":
                if i == 0:
                    e += "M1马达故障"
                elif i == 1:
                    e += "M2马达故障"
                elif i == 2:
                    e += "温度传感器故障"
                elif i == 3:
                    e += "湿度传感器故障"
        if m1_status == "0" and m2_status == "0" and tem_status == "0" and hum_status == "0":
            e = "正常"
        self.Error_Code = e
        _LOGGER.info("Mode: " + str(self._mode) + "M1_speed: " + str(self._speed) + "M2_speed: " + str(self._speed) + "Temper: " + str(self.Temper) + "Humidity: " + str(self.Humidity) + "ErrorCode: " + str(self.Error_Code))


