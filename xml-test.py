import sys
import os

# Add the 'lib' directory to the module search path
sys.path.append(os.path.join(os.path.dirname(__file__), 'Lib'))

# Import the manually added module
import requests
import datetime
import socket
import uuid

request_type = "request_data"
scancode = "830569527899"
mode = "Request"
host = "192.20.10.1"
port = 10080
hostname = "ksskringdistance01"
targethost = "kssksun01"
tident = "P8378691"
sdistance = "20"

def get_mac_address():
    # Retrieve the MAC address of the machine
    mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
    return '-'.join([mac[e:e+2] for e in range(0, 12, 2)])

def connect_server(scancode, host, port, next_callback):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:

        client.connect((host, port))
        print("TCP connection established with the server.")

        xml_data = create_xml_request(scancode)

        with open(os.path.join(os.getcwd(), "request.xml"), "w") as request_file:
            request_file.write(xml_data)


        client.sendall(xml_data.encode('utf-8'))


        data = ""
        while True:
            chunk = client.recv(4096).decode('utf-8')
            data += chunk
            if "</krosy>" in chunk or data.strip() == "ack":
                break


        client.close()
        print("TCP connection closed.")


        next_callback(data)

    except socket.error as e:
        print(f"Error on connection: {e}")
        client.close()


        if mode == "Result":
            print("Failed checkpoint.")
        elif mode == "Request":
            print(f"Failed request for scancode: {scancode}")

def send_request(xml_data, url):
    headers = {'Content-Type': 'application/xml'}
    try:
        response = requests.post(url, data=xml_data, headers=headers, timeout=1)
        response.raise_for_status()
        with open("response.txt", "w") as file:
            file.write(response.text)
        return response.text
    except requests.exceptions.RequestException as e:
        with open("response.txt", "w") as file:
            file.write(str(e))
        return str(e)

def create_xml_request(scancode):
    mac_address = get_mac_address()
    
    ip_address = socket.gethostbyname("ksskringdistance01")
    timestamp = datetime.datetime.now().isoformat(timespec="seconds")

    xml_request_data = f"""
    <krosy>
        <header>
            <sourcehost>
                <requestid>1</requestid>
                <hostname>{hostname}</hostname>
                <ip>{ip_address}</ip>
                <macaddress>{mac_address}</macaddress>
            </sourcehost>
        <targethost>
            <hostname>{targethost}</hostname>
        </targethost>
        </header>
        <body device="{hostname}" ordercount="1">
            <order id="1" scancode="{scancode}" type="1" state="1" timestamp="{timestamp}"/>
        </body>
    </krosy>
    """

    xml_request_io = f"""
    <krosy>
        <header>
            <sourcehost>
                <requestid>2</requestid>
                <hostname>{hostname}</hostname>
                <ip>{ip_address}</ip>
                <macaddress>{mac_address}</macaddress>
            </sourcehost>
            <targethost>
                <hostname>{targethost}</hostname>
            </targethost>
        </header>
        <body device="{hostname}" ordercount="1">
            <order id="1" type="2" state="3" scancode="{scancode}" timestamp="{timestamp}" amountok="1">
                <result>
                    <objects objectcount="1">
                        <object id="1" state="3">
                                <terminal ident="{tident}" distance="{sdistance}">
                                </terminal>
                        </object>
                    </objects>
                </result>		
            </order>
        </body>
    </krosy>
    """

    xml_request_nio = f"""
    <krosy>
        <header>
            <sourcehost>
                <requestid>3</requestid>
                <hostname>{hostname}</hostname>
                <ip>{ip_address}</ip>
                <macaddress>{mac_address}</macaddress>
            </sourcehost>
            <targethost>
                <hostname>{targethost}</hostname>
            </targethost>
        </header>
        <body device="{hostname}" ordercount="1">
            <order id="1" type="2" state="-101" scancode="{scancode}" timestamp="{timestamp}" amountok="0">
                <errors errorcount="1" langu="en">
                    <error id="1" message="Process with failure"/> 
                </errors>
                <result>
                    <objects objectcount="1">
                        <object id="1" state="-135">					
                            <errors errorcount="1" langu="en">					
                                <error id="1" message="motor has an error"/>
                            </errors>
                            <terminal ident="{tident}" distance="{sdistance}">
                                </terminal>
                        </object>
                    </objects>
                </result>		
            </order>
        </body>
    </krosy>
    """
    
    return xml_request_data

if __name__ == "__main__":

    def handle_response(response_data):
        # Save the response to a file
        with open(os.path.join(os.getcwd(), "response.xml"), "w") as response_file:
            response_file.write(response_data)

        print("Response received:")
        print(response_data)

    connect_server(scancode, host, port, handle_response)