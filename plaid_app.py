from flask import jsonify

import plaid

from plaid.api import plaid_api

from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from plaid.model.country_code import CountryCode

from plaid.configuration import Configuration
from plaid.api_client import ApiClient


config = Configuration(
    host=plaid.Environment.Sandbox,
    api_key={
        "clientId": "65d121abf86328001b48a2b2",
        "secret": "78a6e098682f153b1b63f0359e373c",
    }
)

api_client = plaid.ApiClient(config)
client = plaid_api.PlaidApi(api_client)

def get_link(uid):
    request = LinkTokenCreateRequest(
        user=LinkTokenCreateRequestUser(client_user_id=uid),
        client_name="Better Bets",
        country_codes=[CountryCode("US")],
        redirect_uri="https://localhost:3000/plaid",
        language="en",
        products=[Products("auth")],
    )
    response = client.link_token_create(request)
    return response.link_token

access_token = None
item_id = None

def get_access(uid):
    global access_token
    public_token = request.form['public_token']
    request = ItemPublicTokenExchangeRequest(
        public_token=public_token
    )
    response = client.item_public_token_exchange(request)

    # These values should be saved to a persistent database and
    # associated with the currently signed-in user

    return response['access_token'], response['item_id']