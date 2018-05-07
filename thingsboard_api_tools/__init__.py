import json, requests, time
from http import HTTPStatus


class TbApi:

    def __init__(self, url, username, password, token_timeout=600):  # 10 minutes
        self.mothership_url = url
        self.username = username
        self.password = password
        self.token_timeout = token_timeout  # In seconds

        self.token_time = 0
        self.token = None

        self.verbose = False


    ''' Fetches and return an access token needed by most other methods; caches tokens for reuse '''
    def get_token(self):

        # If we already have a valid token, use it
        if self.token is not None and time.time() - self.token_time < self.token_timeout:
            return self.token

        data = '{"username":"' + self.username + '", "password":"' + self.password + '"}'
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
        # json = post("/api/auth/login", None, data, "Error requesting token")

        url = self.mothership_url + "/api/auth/login"
        response = requests.post(url, data=data, headers=headers)
        self.validate_response(response, "Error requesting token")

        self.token = json.loads(response.text)["token"]
        self.token_time = time.time()

        return self.token


    ''' Return a list of all customers in the system '''
    def get_users(self):
        return self.get('/api/customers?limit=99999', "Error retrieving customers")["data"]


    ''' Get customer with specified name '''
    def get_customer(self, name):
        customers = self.get('/api/customers?limit=99999&textSearch=' + name, "Can't find customer with name'" + name + "'")
        for customer in customers['data']:
            if(customer['title'] == name):
                return customer

        return None


    ''' Returns UUID of public customer, or None if there is none '''
    def get_public_user_uuid(self):
        return self.get_user_uuid('public')


    ''' Returns UUID of named customer, or None if user not found '''
    def get_user_uuid(self, name):
        return self.get_id(self.get_customer(name))

    def get_customer_by_id(self, cust_id):
        return self.get('/api/customer/' + cust_id, "Could not retrieve customer with id '" + cust_id + "'")


    ''' Updates an existing customer record '''
    def update_customer(self, cust=None, name=None, address=None, address2=None, city=None, state=None, zip=None, country=None, email=None, phone=None):
        # Check if user passed a customer_id; if so, retrieve the customer object
        if isinstance(cust, str):
            cust = self.get_customer_by_id(cust)

        if name is not None:
            cust["title"] = name
        if address is not None:
            cust["address"] = address
        if address2 is not None:
            cust["address2"] = address2
        if city is not None:
            cust["city"] = city
        if state is not None:
            cust["state"] = state
        if zip is not None:
            cust["zip"]= zip
        if country is not None:
            cust["country"] = country
        if email is not None:
            cust["email"] = email
        if phone is not None:
            cust["phone"] = phone

        return self.post('/api/customer', cust, "Error updating customer")

    ''' Adds customer and returns JSON customer from database '''
    def add_customer(self, name, address, address2, city, state, zip, country, email, phone):
        data = {
            "title": name,
            "address": address,
            "address2": address2,
            "city": city,
            "state": state,
            "zip": zip,
            "country": country,
            "email": email,
            "phone": phone
        }

        return self.post('/api/customer', data, "Error adding customer '" + name + "'")


    ''' Returns true if successful, False if the customer wasn't found '''
    def delete_customer_by_id(self, id):
        return self.delete("/api/customer/" + id, "Error deleting customer '" + id + "'")


    ''' Returns True if successful, False if the customer wasn't found '''
    def delete_customer_by_name(self, name):
        id = self.get_user_uuid(name)
        if id == None:
            print("Could not find customer with name " + name)
            return False

        return self.delete_customer_by_id(id)


    ''' Returns dashboard definition '''
    def assign_dash_to_user(self, dashboard_id, customer_id):
        return self.post('/api/customer/' + customer_id + '/dashboard/' + dashboard_id, None, "Could not assign dashboard '" + dashboard_id + "' to customer '" + customer_id + "'")


    ''' Returns True if dashboard was deleted, False if it did not exist '''
    def delete_dashboard(self, dashboard_id):
        return self.delete('/api/dashboard/' + dashboard_id, "Error deleting dashboard '" + dashboard_id +"'")


    ''' Returns dashboard definition '''
    def create_dashboard_for_customer(self, dash_name, dash_def):

        data = {
            "configuration": dash_def["configuration"],
            "title": dash_name,
            "name": dash_name
        }

        # Update the configuration

        return self.post('/api/dashboard', data, "Error creating new dashboard")


    ''' Returns dashboard with specified name, or None if we can't find one '''
    def get_dashboard_by_name(self, dash_name):
        dashes = self.get('/api/tenant/dashboards?limit=99999&textSearch=' + dash_name, "Error retrieving dashboard '" + dash_name + "'")['data']
        for dash in dashes:
            if dash['title'] == dash_name:
                return dash

        return None


    ''' Retrieve dashboard by id '''
    def get_dashboard_by_id(self, dash_id):
        return self.get('/api/dashboard/info/' + dash_id, "Error retrieving dashboard '" + dash_id + "'")


    def get_dashboard_definition(self, dash_id):
        return self.get('/api/dashboard/' + dash_id, "Error retrieving dashboard definition '" + dash_id + "'")


    ''' Returns named device object, or None if it can't be found '''
    def get_device_by_name(self, device_name):
        devices = self.get('/api/tenant/devices?limit=99999&textSearch=' + device_name, "Error fetching device list with search param '" + device_name + "'")['data']
        for device in devices:
            if device['name'] == device_name:
                return device

        return None


    ''' Returns device object '''
    def add_device(self, device_name, device_type, shared_attributes, server_attributes):

        data = {
            "name": device_name,
            "type": device_type,
        }

        device = self.post('/api/device', data, "Error adding device")
        device_id = self.get_id(device)

        if server_attributes is not None:
            self.set_server_attributes(device_id, server_attributes)

        if shared_attributes is not None:
            self.set_shared_attributes(device_id, shared_attributes)
        
        return device


    def get_device_token(self, device_id):
        json = self.get("/api/device/" + device_id + "/credentials", "Error retreiving device_key for device '" + device_id + "'")
        return json["credentialsId"]


    def get_server_attributes(self, device_id):
        return self.get_attributes(device_id, 'SERVER_SCOPE')


    def get_shared_attributes(self, device_id):
        return self.get_attributes(device_id, 'SHARED_SCOPE')


    def get_client_attributes(self, device_id):
        return self.get_attributes(device_id, 'CLIENT_SCOPE')


    def get_attributes(self, device_id, scope):
        return self.get("/api/plugins/telemetry/DEVICE/" + device_id + "/values/attributes/" + scope, "Error retrieving " + scope + " attributes for '" + device_id + "'")


    def set_server_attributes(self, device_id, attributes):
        return self.set_attributes(device_id, attributes, 'SERVER_SCOPE')


    def set_shared_attributes(self, device_id, attributes):
        return self.set_attributes(device_id, attributes, 'SHARED_SCOPE')


    def set_client_attributes(self, device_id, attributes):
        return self.set_attributes(device_id, attributes, 'CLIENT_SCOPE')


    def set_attributes(self, device_id, attributes, scope):
        return self.post('/api/plugins/telemetry/DEVICE/' + device_id + '/' + scope, attributes, "Error setting " + scope + " attributes for device '" + device_id + "'")



    # Note that this requires the device's secret token, not the device_id!
    def send_telemetry(self, device_token, data, timestamp):
        if timestamp is not None:
            data = {"ts": timestamp ,"values": data }
        return self.post("/api/v1/" + device_token + "/telemetry", data, "Error sending telemetry for device with token '" + device_token + "'")


    def get_telemetry_keys(self, device_id):
        return self.get("/api/plugins/telemetry/DEVICE/" + device_id + "/keys/timeseries", "Error retrieving telemetry keys for device '" + device_id + "'")


    # Pass a single key, a stringified comma-separate list, a list object, or a touple
    def get_latest_telemetry(self, device_id, telemetry_keys):
        if isinstance(telemetry_keys, str):
            keys = telemetry_keys
        else:
            keys = ','.join(telemetry_keys)

        return self.get("/api/plugins/telemetry/DEVICE/" + device_id + "/values/timeseries?keys=" + keys, "Error retrieving latest telemetry for device '" + device_id + "' with keys '" + keys + "'")

    # Pass a single key, a stringified comma-separate list, a list object, or a touple
    def get_telemetry(self, device_id, telemetry_keys, startTime=None, endTime=None, interval=None, limit=None, agg=None):

        if isinstance(telemetry_keys, str):
            keys = telemetry_keys
        else:
            keys = ','.join(telemetry_keys)

        if startTime is None:
            startTime = 0

        if endTime is None:
            endTime = int(time.time() * 1000)       # Unix timestamp, now, convert to milliseconds

        if interval is None:
            interval = 60000   # in ms

        if limit is None:            
            limit = 100

        if agg is None:
            agg = "NONE"   # MIN, MAX, AVG, SUM, COUNT, NONE

        return self.get("/api/plugins/telemetry/DEVICE/" + device_id + "/values/timeseries?keys=" + keys + "&startTs=" + str(int(startTime)) + "&endTs=" + str(int(endTime)) + "&interval=" + str(interval) + "&limit=" + str(limit) + "&agg=" + agg, "Error retrieving telemetry for device '" + device_id + "' with date range '" + str(int(startTime)) + "-" + str(int(endTime)) + "' and keys '" + keys + "'")


    def delete_telemetry(self, device_id, key, timestamp):
        return self.delete("/api/plugins/telemetry/DEVICE/" + device_id + "/timeseries/values?key=" + key + "&ts=" + str(int(timestamp)), "Error deleting telemetry for device '" + device_id + "'")


    ''' Works with Customers, Devices, Dashes '''
    @staticmethod
    def get_id(obj):
        if obj is None:
            return None

        return obj['id']['id']


    def assign_device_to_public_user(self, device_id):
        return self.post('/api/customer/public/device/' + device_id, None, "Error assigning device '" + device_id + "' to public customer")


    ''' Returns True if device was deleted, False if it did not exist '''
    def delete_device(self, device_id):
        return self.delete('/api/device/' + device_id, "Error deleting device '" +  device_id +"'")


    @staticmethod    
    def pretty_print_request(req):
        print('{}\n{}\n{}\n\n{}'.format('-----------START-----------', req.method + ' ' + req.url, '\n'.join('{}: {}'.format(k, v) for k, v in req.headers.items()), req.body, ))


    ''' Modifies headers '''
    def add_auth_header(self, headers):
        token = self.get_token()
        if token is not None:
            headers['X-Authorization'] = 'Bearer ' + token
            
        

    def get(self, params, msg):
        url = self.mothership_url + params
        headers = {'Accept': 'application/json'}
        self.add_auth_header(headers)

        if self.verbose:
            req = requests.Request('GET', url, headers=headers)
            prepared = req.prepare()
            TbApi.pretty_print_request(prepared)

        response = requests.get(url, headers=headers)
        self.validate_response(response, msg)

        return json.loads(response.text)


    def delete(self, params, msg):
        url = self.mothership_url + params
        headers = {'Accept': 'application/json'}
        self.add_auth_header(headers)

        if self.verbose:
            req = requests.Request('DELETE', url, headers=headers)
            prepared = req.prepare()
            TbApi.pretty_print_request(prepared)

        response = requests.delete(url, headers=headers)

        # Don't fail if not found
        if(response.status_code == HTTPStatus.NOT_FOUND):
            return False

        self.validate_response(response, msg)

        return True


    def post(self, params, data, msg):
        url = self.mothership_url + params
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
        self.add_auth_header(headers)

        if self.verbose:
            req = requests.Request('POST', url, json=data, headers=headers)
            prepared = req.prepare()
            TbApi.pretty_print_request(prepared)

        response = requests.post(url, json=data, headers=headers)
        self.validate_response(response, msg)

        if response.text is None or response.text == "":
            return { }

        return json.loads(response.text)


    @staticmethod
    def validate_response(response, msg):
        try:
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(msg + "! " + str(e))
            print("----- BEGIN RESPONSE BODY -----")
            print(response.content)
            print("----- END RESPONSE BODY -----")
            raise
