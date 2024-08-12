# import requests
# from flask import Flask, request, jsonify

# class MpesaClient:
#     def __init__(self, consumer_key, consumer_secret, shortcode, lipa_na_mpesa_online_shortcode, lipa_na_mpesa_online_shortcode_key):
#         self.consumer_key = consumer_key
#         self.consumer_secret = consumer_secret
#         self.shortcode = shortcode
#         self.lipa_na_mpesa_online_shortcode = lipa_na_mpesa_online_shortcode
#         self.lipa_na_mpesa_online_shortcode_key = lipa_na_mpesa_online_shortcode_key

#     def get_access_token(self):
#         api_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
#         response = requests.get(api_url, auth=(self.consumer_key, self.consumer_secret))
#         if response.status_code == 200:
#             json_response = response.json()
#             return json_response['access_token']
#         else:
#             raise Exception("Could not get access token: " + response.text)

#     def stk_push(self, phone_number, amount, account_reference, transaction_desc, callback_url):
#         access_token = self.get_access_token()  # Get the access token
#         url = "https://sandbox.safaricom.co.ke/v1/payment/request"
#         headers = {
#             "Authorization": f"Bearer {access_token}",
#             "Content-Type": "application/json"
#         }
#         payload = {
#             "BusinessShortCode": self.shortcode,
#             "TransactionType": "CustomerPayBillOnline",
#             "Amount": amount,
#             "PartyA": phone_number,
#             "PartyB": self.lipa_na_mpesa_online_shortcode,
#             "PhoneNumber": phone_number,
#             "CallBackURL": callback_url,
#             "AccountReference": account_reference,
#             "TransactionDesc": transaction_desc
#         }

#         response = requests.post(url, json=payload, headers=headers)
#         if response.status_code == 200:
#             return response.json()  # Return the JSON response from the M-Pesa API
#         else:
#             raise Exception("STK push failed: " + response.text)  

# app = Flask(__name__)

# # Initialize your MpesaClient with actual credentials
# mpesa_client = MpesaClient(
#     consumer_key='YOUR_CONSUMER_KEY',
#     consumer_secret='YOUR_CONSUMER_SECRET',
#     shortcode='YOUR_SHORTCODE',
#     lipa_na_mpesa_online_shortcode='YOUR_LIPA_NA_MPESA_SHORTCODE',
#     lipa_na_mpesa_online_shortcode_key='YOUR_LIPA_NA_MPESA_SHORTCODE_KEY'
# )

# @app.route('/stk_push', methods=['GET'])
# def stk_push():
#     # Retrieve parameters from the request
#     phone_number = request.args.get('phone_number', '0746411462')
#     amount = request.args.get('amount', 10, type=int)
#     account_reference = 'Laurine'
#     transaction_desc = 'Description'
#     callback_url = 'https://api.darajambili.com/express-payment'
    
#     try:
#         # Call the stk_push method on the MpesaClient instance
#         response = mpesa_client.stk_push(phone_number, amount, account_reference, transaction_desc, callback_url)
#         return jsonify(response), 200  
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500  

# if __name__ == '__main__':
#     app.run(debug=True)


#Mpesa stk
from flask import Flask, request
import requests
from requests.auth import HTTPBasicAuth
import json
from datetime import datetime
import base64

app = Flask(__name__)

base_url = ''
consumer_key = ''
consumer_secret = ''


@app.route('/mpesa')
def home():
    return 'Hello World!'

@app.route('/access_token')
def get_access_token():
    consumer_key = consumer_key
    consumer_secret = consumer_secret
    endpoint = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'

    r = requests.get(endpoint, auth=HTTPBasicAuth(consumer_key, consumer_secret))
    data = r.json()
    return data['access_token']

@app.route('/register')
def register_urls():
    endpoint = 'https://sandbox.safaricom.co.ke/mpesa/c2b/v1/registerurl'
    access_token = _access_token()
    my_endpoint = base_url + "c2b/"
    headers = { "Authorization": "Bearer %s" % access_token }
    r_data = {
        "ShortCode": "600383",
        "ResponseType": "Completed",
        "ConfirmationURL": my_endpoint + 'con',
        "ValidationURL": my_endpoint + 'val'
    }

    response = requests.post(endpoint, json = r_data, headers = headers)
    return response.json()


@app.route('/simulate')
def test_payment():
    endpoint = 'https://sandbox.safaricom.co.ke/mpesa/c2b/v1/simulate'
    access_token = _access_token()
    headers = { "Authorization": "Bearer %s" % access_token }

    data_s = {
        "Amount": 100,
        "ShortCode": "600383",
        "BillRefNumber": "test",
        "CommandID": "CustomerPayBillOnline",
        "Msisdn": "254708374149"
    }

    res = requests.post(endpoint, json= data_s, headers = headers)
    return res.json()

@app.route('/b2c')
def make_payment():
    endpoint = 'https://sandbox.safaricom.co.ke/mpesa/b2c/v1/paymentrequest'
    access_token = _access_token()
    headers = { "Authorization": "Bearer %s" % access_token }
    my_endpoint = base_url + "/b2c/"

    data = {
        "InitiatorName": "apitest342",
        "SecurityCredential": "SQFrXJpsdlADCsa986yt5KIVhkskagK+1UGBnfSu4Gp26eFRLM2eyNZeNvsqQhY9yHfNECES3xyxOWK/mG57Xsiw9skCI9egn5RvrzHOaijfe3VxVjA7S0+YYluzFpF6OO7Cw9qxiIlynYS0zI3NWv2F8HxJHj81y2Ix9WodKmCw68BT8KDge4OUMVo3BDN2XVv794T6J82t3/hPwkIRyJ1o5wC2teSQTgob1lDBXI5AwgbifDKe/7Y3p2nn7KCebNmRVwnsVwtcjgFs78+2wDtHF2HVwZBedmbnm7j09JO9cK8glTikiz6H7v0vcQO19HcyDw62psJcV2c4HDncWw==",
        "CommandID": "BusinessPayment",
        "Amount": "200",
        "PartyA": "601342",
        "PartyB": "254708374149",
        "Remarks": "Pay Salary",
        "QueueTimeOutURL": my_endpoint + "timeout",
        "ResultURL": my_endpoint + "result",
        "Occasion": "Salary"
    }

    res = requests.post(endpoint, json = data, headers = headers)
    return res.json()

@app.route('/lnmo')
def init_stk():
    endpoint = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
    access_token = _access_token()
    headers = { "Authorization": "Bearer %s" % access_token }
    my_endpoint = 'https://mydomain.com/path' + "/lnmo"
    Timestamp = datetime.now()
    times = Timestamp.strftime("%Y%m%d%H%M%S")
    password = "174379" + "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919" + times
    datapass = base64.b64encode(password.encode('utf-8'))

    data = {
        "BusinessShortCode": "174379",
        "Password": datapass,
        "Timestamp": times,
        "TransactionType": "CustomerPayBillOnline",
        "PartyA": "254708374149", # fill with your phone number
        "PartyB": "174379",
        "PhoneNumber": "254746411462", # fill with your phone number
        "CallBackURL": my_endpoint,
        "AccountReference": "TestPay",
        "TransactionDesc": "HelloTest",
        "Amount": 2
    }

    res = requests.post(endpoint, json = data, headers = headers)
    return res.json()

@app.route('/lnmo', methods=['POST'])
def lnmo_result():
    data = request.get_data()
    f = open('lnmo.json', 'a')
    f.write(data)
    f.close()

@app.route('/b2c/result', methods=['POST'])
def result_b2c():
    data = request.get_data()
    f = open('b2c.json', 'a')
    f.write(data)
    f.close()

@app.route('/b2c/timeout', methods=['POST'])
def b2c_timeout():
    data = request.get_json()
    f = open('b2ctimeout.json', 'a')
    f.write(data)
    f.close()

@app.route('/c2b/val', methods=['POST'])
def validate():
    data = request.get_data()
    f = open('data_v.json', 'a')
    f.write(data)
    f.close()

@app.route('/c2b/con', methods=['POST'])
def confirm():
    data = request.get_json()
    f = open('data_c.json', 'a')
    f.write(data)
    f.close()


def _access_token():
    consumer_key = consumer_key
    consumer_secret = consumer_secret
    endpoint = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'

    r = requests.get(endpoint, auth=HTTPBasicAuth(consumer_key, consumer_secret))
    data = r.json()
    return data['access_token']


if __name__ == "__main__":
    app.run(port=5000, debug=True)
