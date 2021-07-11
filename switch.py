import sys, yaml
from systemd import journal
import logging
import wyze_sdk
from wyze_sdk.errors import WyzeApiError

# Configuring wyze_sdk to be less noisy in the logs. Change this to a different log level if you need to troubleshoot.
wyze_sdk.set_stream_logger('wyze_sdk', level=logging.WARNING)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger('wyzeplug_switch')
log.addHandler(journal.JournaldLogHandler())
log.info("Starting switch.py.")
log.info("Finished configuring logger.")

# Open a connection to the Wyze API with values loaded from config file.
log.info("Loading configuration.")
configuration = yaml.load(open('config', 'r'), Loader=yaml.Loader)
log.info("Configuration loaded.")
log.info("Connected to Wyze API and retrieving devices..")
wyze_client = wyze_sdk.Client(email=configuration['wyze']['email'], password=configuration['wyze']['password'])
wyze_devices = wyze_client.devices_list()
log.info("Device list retrieved.")

def find_device(device_nick):
    """
    Function to search Wyze API for a device with a name equal to device_nick (str). Returns plug object.
    """
    devicefound = False
    log.debug("Searching for device {}".format(device_nick))
    try:
        for device in wyze_devices:
            if device.nickname == sys.argv[2]:
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


def turn_on(plug):
    """
    Turns on plug (obj). Plug is an object returned from the find_device function.
    """
    log.info("Turned on plug {} ondemand.".format(plug.nickname))
    wyze_client.plugs.turn_on(device_mac=plug.mac, device_model=plug.product.model)


def turn_off(plug):
    """
    Turns off plug (obj). Plug is an object returned from the find_device function.
    """
    log.info("Turned off plug {} ondemand.".format(plug.nickname))
    wyze_client.plugs.turn_off(device_mac=plug.mac, device_model=plug.product.model)


def toggle(plug):
    """
    Finds the state of a plug (obj) and toggles between on/off states. Plug is an object returned from the find_device function.
    """
    log.info("Toggling plug {} ondemand.".format(plug.nickname))
    if plug.is_on:
        turn_off(plug)
    elif not plug.is_on:
        turn_on(plug)


if sys.argv[1] in ('--on', '--off', '--toggle') and sys.argv[2]:
    log.info("Switch started in on-demand mode.")
    plug = find_device(sys.argv[1])
    if sys.argv[1] == "--on":
        turn_on(plug)
    elif sys.argv[1] == "--off":
        turn_off(plug)
    elif sys.argv[1] == "--toggle":
        toggle(plug)
else:
    raise Exception("Invalid option.")
log.info("Execution complete.")