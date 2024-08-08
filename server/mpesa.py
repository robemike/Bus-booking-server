import requests
from flask import Flask, request, jsonify

class MpesaClient:
    def __init__(self, consumer_key, consumer_secret, shortcode, lipa_na_mpesa_online_shortcode, lipa_na_mpesa_online_shortcode_key):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.shortcode = shortcode
        self.lipa_na_mpesa_online_shortcode = lipa_na_mpesa_online_shortcode
        self.lipa_na_mpesa_online_shortcode_key = lipa_na_mpesa_online_shortcode_key

    def get_access_token(self):
        api_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
        response = requests.get(api_url, auth=(self.consumer_key, self.consumer_secret))
        if response.status_code == 200:
            json_response = response.json()
            return json_response['access_token']
        else:
            raise Exception("Could not get access token: " + response.text)

    def stk_push(self, phone_number, amount, account_reference, transaction_desc, callback_url):
        access_token = self.get_access_token()  # Get the access token
        url = "https://sandbox.safaricom.co.ke/v1/payment/request"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "BusinessShortCode": self.shortcode,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone_number,
            "PartyB": self.lipa_na_mpesa_online_shortcode,
            "PhoneNumber": phone_number,
            "CallBackURL": callback_url,
            "AccountReference": account_reference,
            "TransactionDesc": transaction_desc
        }

        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            return response.json()  # Return the JSON response from the M-Pesa API
        else:
            raise Exception("STK push failed: " + response.text)  

app = Flask(__name__)

# Initialize your MpesaClient with actual credentials
mpesa_client = MpesaClient(
    consumer_key='YOUR_CONSUMER_KEY',
    consumer_secret='YOUR_CONSUMER_SECRET',
    shortcode='YOUR_SHORTCODE',
    lipa_na_mpesa_online_shortcode='YOUR_LIPA_NA_MPESA_SHORTCODE',
    lipa_na_mpesa_online_shortcode_key='YOUR_LIPA_NA_MPESA_SHORTCODE_KEY'
)

@app.route('/stk_push', methods=['GET'])
def stk_push():
    # Retrieve parameters from the request
    phone_number = request.args.get('phone_number', '0746411462')
    amount = request.args.get('amount', 10, type=int)
    account_reference = 'Laurine'
    transaction_desc = 'Description'
    callback_url = 'https://api.darajambili.com/express-payment'
    
    try:
        # Call the stk_push method on the MpesaClient instance
        response = mpesa_client.stk_push(phone_number, amount, account_reference, transaction_desc, callback_url)
        return jsonify(response), 200  
    except Exception as e:
        return jsonify({"error": str(e)}), 500  

if __name__ == '__main__':
    app.run(debug=True)
