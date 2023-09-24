# ! /usr/bin/env python3.6
"""
Python 3.6 or newer required.
"""
import json
import os
from dotenv import load_dotenv
import stripe
import requests
from flask import Flask, render_template, jsonify, request, send_file

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__, static_folder='public', static_url_path='/public', template_folder='templates')

# This is your test secret API key.
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')


@app.route('/')
def test():
    return render_template('test.html')


def calculate_order_amount(items):
    # Replace this constant with a calculation of the order's amount
    # Calculate the order total on the server to prevent
    # people from directly manipulating the amount on the client
    # Define the data you want to send as JSON
    items = 1500 + 9  # Example value, replace with your calculation logic
    return 1400


@app.route('/create-payment-intent', methods=['POST'])
def create_payment():
    try:
        data = request.get_json()
        if data is None:
            return jsonify(error="Request data is not in JSON format"), 415
        # Verify that 'items' key exists in the JSON data
        if 'items' in data:
            # Create a PaymentIntent with the order amount and currency
            intent = stripe.PaymentIntent.create(
                amount=calculate_order_amount(data['items']),
                currency='eur',
                # In the latest version of the API, specifying the `automatic_payment_methods` parameter is optional because Stripe enables its functionality by default.
                automatic_payment_methods={
                    'enabled': True,
                },
            )
            return jsonify({
                'clientSecret': intent['client_secret']
            })
        else:
            return jsonify(error="Missing 'items' key in JSON data"), 400
    except Exception as e:
        return jsonify(error=str(e)), 400


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5005)
