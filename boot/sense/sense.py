import requests
import time
import math
import board
import busio
import socket
import logging
import adafruit_ads1x15.ads1015 as ADS
import Adafruit_DHT
import yaml
from adafruit_ads1x15.analog_in import AnalogIn
import psycopg2

config = yaml.safe_load(open("/home/pi/sense/sense.yml"))

LOG_LEVEL = logging.INFO
LOG_FILE = "/var/log/sense.log"
LOG_FORMAT = "%(asctime)s %(levelname)s %(message)s"
logging.basicConfig(filename=LOG_FILE, format=LOG_FORMAT, level=LOG_LEVEL)

numSamples=250
threshold=100

i2c = ads = chan = pgConn = dhtDevice = None
try:
    if (config['sensors']['current-transducer']['enabled']):
        i2c = busio.I2C(board.SCL, board.SDA)

        # Create the ADC object using the I2C bus
        ads = ADS.ADS1015(i2c)

        # Create differential input between channel 0 and 1
        chan = AnalogIn(ads, ADS.P0, ADS.P1)
except Exception as e:
    logging.exception('No ADS found, will not measure current')

def refreshPGConnection():

    global pgConn
    if (pgConn is None or pgConn.closed > 0):
        pgConn = psycopg2.connect(
            host=config['database']['host'],
            database=config['database']['database'],
            user=config['database']['user'],
            password=config['database']['password'])
    return pgConn

def safeClosePGConn():
    if pgConn is not None and pgConn.closed == 0:
        pgConn.close()

def postSensorData(eventName, sensorValue):
    try:
        refreshPGConnection()
        cur = pgConn.cursor()
        sql = """INSERT INTO t_sensor_update(sensor_ts,host,key,value) values (to_timestamp(%s), %s, %s, %s)"""
        cur.execute(sql, (int(time.time()), socket.gethostname(), socket.gethostname() + "." + eventName, sensorValue))
        pgConn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        logging.exception('Exception saving data to db %s', error)
    #url = "https://maker.ifttt.com/trigger/sensor-post/with/key/biz-56mjM-89gdDun4gUjq"
    #data = {'value1': time.time(), 'value2': socket.gethostname() + "." + eventName, 'value3': sensorValue}
    logging.info(f'Logged {eventName} {sensorValue}')
    #logging.info(requests.post(url, data))

def recordDHT():
    try:
        logging.info('Checking temp')
        humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.AM2302, 22)
        postSensorData('temperature_f', temperature*9/5 + 32 + config['sensors']['thermister']['offset'])
        postSensorData('humidity', humidity)
    except Exception as e:
        logging.info('DHT Sensor not found, will not record temperature and humidity')

def sense():
    i = 0
    rms = 0
    lastDHTTime = 0
    logCurrent = False
    isCircuitOn = False
    lastStatusTime = time.time()
    try:
        postSensorData('script.launched', True)
        logging.info(f'Starting with sensor config {config["sensors"]}')
    except Exception as e:
        logging.exception('Exception tr: %s', e)

    while True:
        try:
            delay = 10

            if chan is not None:
                delay = 0

            if (config['sensors']['thermister']['enabled'] and (time.time() - lastDHTTime) > 5*60):
                lastDHTTime = time.time()
                recordDHT()

            i = i + 1
            if (chan is not None):
                value = chan.value
                rms = rms + value*value

                if i>numSamples-1:
                    rms = rms/numSamples
                    rms = math.sqrt(rms)
                    circuitCurrentlyOn = rms > threshold
                    voltage = rms * 0.00005
                    current = voltage * config['sensors']['current-transducer']['max-amps']
                    if (logCurrent):
                        postSensorData('pump.current', current)
                        logCurrent = False
                    if (circuitCurrentlyOn != isCircuitOn):
                        isCircuitOn = circuitCurrentlyOn
                        newStatusTime = time.time()
                        event = 'pump.on' if isCircuitOn else 'pump.off'
                        postSensorData(event, newStatusTime - lastStatusTime)
                        lastStatusTime = newStatusTime
                        if (isCircuitOn):
                            logCurrent = True
                        safeClosePGConn()
                    rms = 0
                    i = 0
                    time.sleep(0.1)
            if (delay > 0):
                time.sleep(delay)
        except Exception as e:
            logging.exception('Exception in sense loop: %s', e)
            time.sleep(1)

def main():
    sense()
    #postSensorData('pump.status', 'on')

if __name__ == "__main__":
  main()
