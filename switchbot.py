import requests, json, time

class Switchbot:
    BASEURL = 'https://api.switch-bot.com'
    def __init__(self, authtoken='', device_name=''):
        if authtoken == '':
            raise Exception("Cannot create Object of class Switchbot without authorization token.")
        self.authmsg = { 'Authorization': '{}'.format(authtoken) }
        # Get the device list
        r = requests.get(self.BASEURL + '/v1.0/devices', headers=self.authmsg)
        self.device_request_response = json.loads(r.content.decode('utf-8'))
        # self.device_request_response = {'statusCode': 100, 'body': {'deviceList': [{'deviceId': 'D8600992765A', 'deviceName': 'Hub Mini', 'deviceType': 'Hub Mini', 'enableCloudService': False, 'hubDeviceId': '000000000000'}, {'deviceId': 'FACB49E7C1FD', 'deviceName': 'Movie Screen', 'deviceType': 'Curtain', 'enableCloudService': True, 'hubDeviceId': 'D8600992765A', 'curtainDevicesIds': ['FACB49E7C1FD'], 'calibrate': True, 'group': False, 'master': True, 'openDirection': 'left'}], 'infraredRemoteList': [{'deviceId': '01-202107201550-64989006', 'deviceName': 'TV', 'remoteType': 'TV', 'hubDeviceId': 'D8600992765A'}]}, 'message': 'success'}

    def get_devices(self):
        """
        Returns a list of Switchbot device names as a List
        """
        device_list = []
        for device in self.device_request_response['body']['deviceList']:
            device_list += [ { 'name': device['deviceName'], 'id': device['deviceId'], 'type': device['deviceType'] } ]
        for device in self.device_request_response['body']['infraredRemoteList']:
            device_list += [ { 'name': device['deviceName'], 'id': device['deviceId'], 'type': device['remoteType'] } ]
        return device_list
        
    def get(self, device_name=None):
        """
        Returns a Switchbot object of as a class object or None if the device name or device id is not found.
        """
        if not device_name:
            return None
        device_list = self.device_request_response['body']['deviceList'] + \
            self.device_request_response['body']['infraredRemoteList']
        for n in range(0,len(device_list)):
            if device_list[n]['deviceName'] == device_name or \
                device_list[n]['deviceId'] == device_name:
                    try:
                        device_type = device_list[n]['deviceType']
                    except KeyError:
                        device_type = device_list[n]['remoteType']
                    if 'Hub' in device_type:
                        return Hub(self.authmsg, device_list[n])
                    elif 'Curtain' in device_type:
                        return Curtain(self.authmsg, device_list[n])
                    elif device_type in ('TV', 'DIY Projector'):
                        return IRRemote(self.authmsg, device_list[n])
                    else:
                        return None
        return None


class Curtain:
    def __init__(self, authmsg, data):
        self.BASEURL = 'https://api.switch-bot.com'
        self.authmsg = authmsg
        self.device_id = data['deviceId']
        self.device_name = data['deviceName']
        self.device_type = data['deviceType']
        self.cloud_enabled = data['enableCloudService']
        self.hub_device_id = data['hubDeviceId']
        self.curtain_devices_ids = data['curtainDevicesIds']
        self.calibrate = data['calibrate']
        self.group = data['group']
        self.master = data['master']
        self.opendirection = data['openDirection']

    def open(self):
        endpoint_url = f'/v1.0/devices/{self.device_id}/commands'
        command = { 'command': 'turnOn' }
        r = requests.post(self.BASEURL + endpoint_url, headers=self.authmsg, json=command)

    def close(self):
        endpoint_url = f'/v1.0/devices/{self.device_id}/commands'
        headers = self.authmsg
        command = { 'command': 'turnOff' }
        r = requests.post(self.BASEURL + endpoint_url, headers=headers, json=command)

    def status(self):
        endpoint_url = f'/v1.0/devices/{self.device_id}/status'
        headers = self.authmsg
        return requests.get(self.BASEURL + endpoint_url, headers=headers)

class Hub:
    def __init__(self, authmsg, data):
        self.BASEURL = 'https://api.switch-bot.com'
        self.authmsg = authmsg
        self.device_id = data['deviceId']
        self.device_name = data['deviceName']
        self.device_type = data['deviceType']
        self.cloud_enabled = data['enableCloudService']
        self.hub_device_id = data['hubDeviceId']

class IRRemote:
    def __init__(self, authmsg, data):
        self.BASEURL = 'https://api.switch-bot.com'
        self.authmsg = authmsg
        self.device_id = data['deviceId']
        self.device_name = data['deviceName']
        self.remote_type = data['remoteType']
        self.hub_device_id = data['hubDeviceId']

    def on(self):
        endpoint_url = f'/v1.0/devices/{self.device_id}/commands'
        headers = self.authmsg
        if "Projector" in self.device_name:
            command = { 'command': 'Power', 'commandType': 'customize' }
            requests.post(self.BASEURL + endpoint_url, headers=headers, json=command)
        else:
            command = { 'command': 'turnOn' }
            requests.post(self.BASEURL + endpoint_url, headers=headers, json=command)

    def off(self):
        endpoint_url = f'/v1.0/devices/{self.device_id}/commands'
        headers = self.authmsg
        if "Projector" in self.device_name:
            command = { 'command': 'Power', 'commandType': 'customize' }
            requests.post(self.BASEURL + endpoint_url, headers=headers, json=command)
            time.sleep(2)
            requests.post(self.BASEURL + endpoint_url, headers=headers, json=command)
        else:
            command = { 'command': 'turnOff' }
            r = requests.post(self.BASEURL + endpoint_url, headers=headers, json=command)

    def status(self):
        endpoint_url = f'/v1.0/devices/{self.device_id}/status'
        headers = self.authmsg
        return requests.get(self.BASEURL + endpoint_url, headers=headers)