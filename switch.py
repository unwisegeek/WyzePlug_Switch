import switchbot
import os, sys, yaml, json
import requests
from systemd import journal
import logging
import wyze_sdk
from wyze_sdk.errors import WyzeApiError

sb_base_url = 'https://api.switch-bot.com'
cached_devices = False
wyze_client = None
sb_client = None

def wyze_login():
    log.info("Establishing a connection to Wyze API")
    userpass = False
    totp_exists = False
    try:
        a = wconf['email']
        b = wconf['password']
    except:
        log.info("No username and password configured for Wyze. Aborting connection to Wyze API.")
        return None
    else:
        userpass = True
    try:
        a = wconf['totp_key']
    except:
        log.info("2FA not configured. Skipping.")
    else:
        totp_exists = True
    
    if userpass and not totp_exists:
        return wyze_sdk.Client(email=wconf['email'], password=wconf['password'])
    elif userpass and totp_exists:
        return wyze_sdk.Client(email=wconf['email'], password=wconf['password'], totp_key=wconf['totp_key'])

def switchbot_login():
    log.info("Establishing connection to Switchbot API")
    return switchbot.Switchbot(sconf['token'])

def wyze_find_device(device_nick, listdevices=False):
    """
    Function to search Wyze API for a device with a name equal to device_nick (str). Returns plug object.
    """
    devicefound = False
    log.debug("Searching for device {}".format(device_nick))
    wyze_client = wyze_login()
    wyze_devices = wyze_client.devices_list()
    device_list = []
    if listdevices:
        for device in wyze_devices:
            device_list += [ device.nickname ]
        return device_list        
    try:
        for device in wyze_devices:
            if device.nickname == device_nick:
                plug = wyze_client.plugs.info(device_mac=device.mac)
                log.debug("Found device {}".format(device_nick))
                return plug
        if not devicefound:
            log.info("Did not find requested device named {} on configured Wyze account.".format(device_nick))
            raise Exception("Named device not found on Wyze account.")
    except WyzeApiError as e:
        # You will get a WyzeApiError is the request failed
        log.debug("Error received from API: {}".format(e))
        print(f"Got an error: {e}")

def switchbot_find_device(device_nick, listdevices=False):
    swbt_client = switchbot_login()
    devicefound = False
    log.debug(f"Searching for device {device_nick}")
    server_device_list = swbt_client.get_devices()
    if listdevices:
        device_list = []
        if server_device_list:
            for i in range(0, len(server_device_list)):
                device_list += [ { 'name': f"{server_device_list[i]['name']}", 'id': f"{server_device_list[i]['id']}", 'type': f"{server_device_list[i]['type']}" } ]
            return device_list
    for i in range(0, len(server_device_list)):
        if device_nick == server_device_list[i]['name'] or \
            device_nick == server_device_list[i]['id']:
            return swbt_client.get(device_name=device_nick)
    
def wyze_turn_on(plug):
    """
    Turns on plug (obj). Plug is an object returned from the find_device function.
    """
    wyze_client = wyze_login()
    log.info("Turned on plug {} ondemand.".format(plug.nickname))
    wyze_client.plugs.turn_on(device_mac=plug.mac, device_model=plug.product.model)

def wyze_turn_off(plug):
    """
    Turns off plug (obj). Plug is an object returned from the find_device function.
    """
    wyze_client = wyze_login()
    log.info("Turned off plug {} ondemand.".format(plug.nickname))
    wyze_client.plugs.turn_off(device_mac=plug.mac, device_model=plug.product.model)

def wyze_toggle(plug):
    """
    Finds the state of a plug (obj) and toggles between on/off states. Plug is an object returned from the find_device function.
    """
    log.info("Toggling plug {} ondemand.".format(plug.nickname))
    if plug.is_on:
        turn_off(plug)
    elif not plug.is_on:
        turn_on(plug)

def load_devices(service='wyze'):
    if os.path.exists('device_cache'):
        devices = yaml.load(open('device_cache', 'r'), Loader=yaml.Loader)
        return devices[service]

def dump_devices(devices):
    # if os.path.exists('device_cache') and type(devices) == "dict":
    #     os.remove('device_cache')
    open('device_cache', 'w').write(yaml.dump(devices))
    if os.path.exists('device_cache'):
        return True
    else:
        return False

def refresh_devices():
    rw = wyze_find_device("", listdevices=True)
    rs = switchbot_find_device("", listdevices=True)
    devices = {}
    devices['wyze'] = rw
    devices['switchbot'] = rs
    if dump_devices(devices):
        log.info("Devices refreshed.")
        return True
    else:
        log.info("Error refreshing devices.")
        return False

def which_service(nick, rw, rs):
    for each in rw:
        if nick in each:
            return "wyze"
    for each in rs:
        if nick in each['name']:
            return "switchbot"
    return None    
    

logging.basicConfig(level=logging.INFO)
log = logging.getLogger('wyzeplug_switch')
configuration = yaml.load(open('config', 'r'), Loader=yaml.Loader)
wconf = configuration['wyze']
mconf = configuration['mqtt']
sconf = configuration['switchbot']

if __name__ == "__main__":
    # Main Logic
    # Configuring wyze_sdk to be less noisy in the logs. Change this to a different log level if you need to troubleshoot.
    wyze_sdk.set_stream_logger('wyze_sdk', level=logging.WARNING)

    logging.basicConfig(level=logging.INFO)
    log = logging.getLogger('wyzeplug_switch')
    log.addHandler(journal.JournaldLogHandler())
    log.info("Starting switch.py.")
    log.info("Finished configuring logger.")

    # Load the configuration - login has been moved to individual functions that need it.
    log.info("Loading configuration.")
    log.info("Configuration loaded.")
    if os.path.exists('device_cache'):
        devices = yaml.safe_load(open('device_cache', 'r'))
        log.info("Found cached device list.")
        cached_devices = True
    else:
        log.info("Cached device list not found. Refreshing device cache.")
        if refresh_devices():
            if os.path.exists('device_cache'):
                devices = yaml.safe_load(open('device_cache', 'r'))
                log.info("Found cached device list.")
                cached_devices = True
        else:
            log.warning("Device refresh failed. Not using cached devices. This will result in more API calls.")
    if (sys.argv[1] in ('--on', '--off', '--toggle', '--close', '--open') and sys.argv[2]) or sys.argv[1] in ("--list", "--refresh"):
        log.info("Switch started in on-demand mode.")
        if sys.argv[1] == "--refresh":
            if refresh_devices():
                log.info("User-requested refresh complete. Exiting.")
                sys.exit()
            else:
                log.info("User requested refresh failed. Exiting.")
                sys.exit()
        if sys.argv[1] == "--list":
            if cached_devices:
                wyze_devices = load_devices('wyze')
                sb_devices = load_devices('switchbot')
            else:
                rw = wyze_find_device("", listdevices=True)
                rs = switchbot_find_device("", listdevices=True)

            print("Wyze Devices")
            print("---- -------")
            for each in wyze_devices:
                print(each)
            print("\nSwitchbot Devices")
            print("--------- ---------")
            for each in sb_devices:
                print(f"{each['name']} ({each['type']})")
            sys.exit()
        if cached_devices:
            rw = load_devices('wyze')
            rs = load_devices('switchbot')
        else:
            rw = wyze_find_device("", listdevices=True)
            rs = switchbot_find_device("", listdevices=True)
        service = which_service(sys.argv[2], rw, rs)
        if service == "wyze":
            plug = wyze_find_device(sys.argv[2])
            if sys.argv[1] == "--on":
                wyze_turn_on(plug)
            elif sys.argv[1] == "--off":
                wyze_turn_off(plug)
            elif sys.argv[1] == "--toggle":
                wyze_toggle(plug)
        if service == "switchbot":
            device = switchbot_find_device(sys.argv[2])
            if sys.argv[1] == "--on":
                device.on()
            if sys.argv[1] == "--off":
                device.off()
            if sys.argv[1] == "--open":
                device.open()
            elif sys.argv[1] == "--close":
                device.close()
    elif sys.argv[1] in ("--daemon", "--server"):
        log.info("Switch started in daemon mode. Press Ctrl-C to exit.")
        import paho.mqtt.client as mqtt
        
        def on_connect(client, userdata, flags, rc):
            log.info("Connected to MQTT broker with result: {}".format(str(rc)))
            client.subscribe(mconf['topic'])

        def on_message(client, userdata, msg):
            message = str(msg.payload.decode('utf-8'))
            command = json.loads(message)
            log.info("Processing message from MQTT: [{}] {}".format(str(msg.topic), message))
            service = which_service(command['name'])
            if service == "wyze":
                device = wyze_find_device(command['name'])
                if command['command'] == "on":
                    wyze_turn_on(device)
                elif command['command'] == "off":
                    wyze_turn_off(device)
                elif command['command'] == "toggle":
                    wyze_toggle(device)
            if service == "switchbot":
                device = switchbot_find_device(command['name'])
                if command['command'] == "on":
                    device.on()
                if command['command'] == "off":
                    device.off()
                if command['command'] == "open":
                    device.open()
                if command['command'] == "close":
                    device.close()
            log.info("Message processing complete.")
        
        mqtt_client = mqtt.Client()
        mqtt_client.on_connect = on_connect
        mqtt_client.on_message = on_message

        mqtt_client.username_pw_set(mconf['user'], password=mconf['password'])
        mqtt_client.connect(mconf['server'], mconf['port'], 60)
        try:
            mqtt_client.loop_forever()
        except KeyboardInterrupt:
            pass
    else:
        raise Exception("Invalid option.")

    log.info("Execution complete.")

