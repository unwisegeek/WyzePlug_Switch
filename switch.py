import sys, wyze_sdk, yaml
from wyze_sdk import Client
from wyze_sdk.errors import WyzeApiError

# Open a connection to the Wyze API with values loaded from config file.
configuration = yaml.load(open('config', 'r'), Loader=yaml.Loader)
wyze_client = Client(email=configuration['wyze']['email'], password=configuration['wyze']['password'])


def find_device(device_nick):
    """
    Function to search Wyze API for a device with a name equal to device_nick (str). Returns plug object.
    """
    devicefound = False
    try:
        response = wyze_client.devices_list()
        for device in wyze_client.devices_list():
            # print(f"mac: {device.mac}")
            # print(f"nickname: {device.nickname}")
            # print(f"is_online: {device.is_online}")
            # print(f"product model: {device.product.model}")
            if device.nickname == sys.argv[2]:
                plug = wyze_client.plugs.info(device_mac=device.mac)
                return plug
        if not devicefound:
            raise Exception("Named device not found on Wyze account.")
    except WyzeApiError as e:
        # You will get a WyzeApiError is the request failed
        print(f"Got an error: {e}")


def turn_on(plug):
    """
    Turns on plug (obj). Plug is an object returned from the find_device function.
    """
    wyze_client.plugs.turn_on(device_mac=plug.mac, device_model=plug.product.model)


def turn_off(plug):
    """
    Turns off plug (obj). Plug is an object returned from the find_device function.
    """
    wyze_client.plugs.turn_off(device_mac=plug.mac, device_model=plug.product.model)


def toggle(plug):
    """
    Finds the state of a plug (obj) and toggles between on/off states. Plug is an object returned from the find_device function.
    """
    if plug.is_on:
        turn_off(plug)
    elif not plug.is_on:
        turn_on(plug)


if sys.argv[1] in ('--on', '--off', '--toggle') and sys.argv[2]:
    plug = find_device(sys.argv[1])
    if sys.argv[1] == "--on":
        turn_on(plug)
    elif sys.argv[1] == "--off":
        turn_off(plug)
    elif sys.argv[1] == "--toggle":
        toggle(plug)
else:
    raise Exception("Invalid option.")