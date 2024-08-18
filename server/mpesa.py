from flask import Flask, request, jsonify
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
import base64

app = Flask(__name__)

my_endpoint = "https://f0f2-41-80-112-198.ngrok-free.app"

@app.route('/')
def home():
    return 'Hello Mpesa!'

@app.route('/api/mpesa-payment', methods=['POST'])
def mpesa_payment():
    try:
        data = request.get_json()  
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400

        amount = data.get('amount')
        phone_number = data.get('phone_number')

        mpesa_response = mpesa_payment(amount, phone_number)
        return jsonify(mpesa_response), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/pay')  
def MpesaExpress():  
    amount = request.args.get('amount')  
    phone_number = request.args.get('phone_number')  

    endpoint = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"  
    access_token = getAccessToken()  

    headers = {  
        'Content-Type': 'application/json',  
        'Authorization': 'Bearer ' + access_token  
    } 
    
    Timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    password = base64.b64encode(f"{174379}{'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919'}{Timestamp}".encode()).decode()

    data = {  
        "BusinessShortCode": "174379",  
        "Password": password,  
        "Timestamp": Timestamp,  
        "TransactionType": "CustomerPayBillOnline",  
        "Amount": amount,  
        "PartyA": phone_number,  
        "PartyB": "174379",  
        "PhoneNumber": phone_number,
        "CallBackURL": my_endpoint + "/lnmo-callback",  
        "AccountReference": "BusLink",  
        "TransactionDesc": "Payment of Bus Ticket"   
    }

    response = requests.post(endpoint, json=data, headers=headers)  
    return response.json()
@app.route('/lnmo-callback', methods=['POST'])
def incoming():
    data = request.get_json()
    print(data)
    return "ok"

def getAccessToken():
    consumer_key = "Xj8JxM66iucQrrtPdhOXG5bTlz3l03lfyIcQ5Y7vDi6TZyJG"
    consumer_secret = "GWdrGgv1faP9PXe066AMD6WIHXMfE7bQqQN6MLJaGgnBz5FdoXZ2hy7ZPwR7TwaI"
    endpoint = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    r = requests.get(endpoint, auth=HTTPBasicAuth(consumer_key, consumer_secret))
    data = r.json()
    return data['access_token']

if __name__ == "__main__":
    app.run(debug=True)



