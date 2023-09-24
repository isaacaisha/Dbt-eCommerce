#! /usr/bin/env python3.6

"""
server.py
Stripe Sample.
Python 3.6 or newer required.
"""
import os
from flask import Flask, redirect, request

import stripe

# This is your test secret API key.
stripe.api_key = \
    'sk_test_51NtGrNCE7CUcTtCeMwpklwKcskF8oJURA1HbZ7YxoPwsCIPaGRSdNcDkR68VTnntxbkLxQtPNOTxgeDudvFL4e3t001bZxAGZn'

app = Flask(__name__,
            static_url_path='/public',
            static_folder='public')

YOUR_DOMAIN = 'http://localhost:4242'


@app.route('/')
def test():
    return 'server.html'


@app.route('/create-checkout-session', methods=['GET', 'POST'])
def create_checkout_session():
    try:
        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    # Provide the exact Price ID (for example, pr_1234) of the product you want to sell
                    'price': '{{evt_1NtgkICE7CUcTtCe5eB9H2hZ}}',
                    'quantity': 1,
                },
            ],
            mode='payment',
            success_url=YOUR_DOMAIN + '/success.html',
            cancel_url=YOUR_DOMAIN + '/cancel.html',
        )
    except Exception as e:
        return str(e)

    return redirect(checkout_session.url, code=303)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=4242)
