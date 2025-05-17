from flask import Flask, render_template, request, jsonify
import requests
import os
import time
from dotenv import load_dotenv
from datetime import datetime,timezone
from web3 import Web3
import json

import logging

logging.basicConfig(
    filename='app.log',          
    level=logging.INFO,           
    format='%(asctime)s - %(levelname)s - %(message)s', 
    filemode='w',
)



load_dotenv()
app = Flask(__name__)
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
QUICKNODE_ENDPOINT_API_KEY = os.getenv("PROJECT_ID")

def get_current_block():
    url = f"https://api.etherscan.io/api?module=proxy&action=eth_blockNumber&apikey={ETHERSCAN_API_KEY}"
    response = requests.get(url)
    data = response.json()
    block_hex = data["result"]
    return int(block_hex,16)


def get_all_transaction(address,start_block,step = 10000, delay=0.2):
    all_transactions = []
    current_block = start_block
    end_block = get_current_block()
    print(f"PROCESSING")
    while current_block <= end_block:
        next_block = current_block+step-1
        if next_block > end_block:
            next_block = end_block
        url = (
                f"https://api.etherscan.io/api"
                f"?module=account&action=txlist"
                f"&address={address}"
                f"&startblock={current_block}"
                f"&endblock={next_block}"
                f"&sort=asc"
                f"&apikey={ETHERSCAN_API_KEY}"
        )

        response = requests.get(url)
        data = response.json()
        raw_transactions = data.get("result", [])

        formatted_transactions = []
        for tx in raw_transactions:
            eth_value = int(tx["value"]) / 1e18
            tx_type = "ETH Transfer" if int(tx["value"]) > 0 else "Contract Interaction"

            formatted_transactions.append({
                "blockNumber": tx["blockNumber"], 
                "hash": tx["hash"],
                "from": tx["from"],
                "to": tx["to"],
                "value": eth_value,
                "type": tx_type,
            })

            if data["status"] != "1":
            #   print(f"Error or not transaction for block range {current_block} - {next_block}")
              logging.error(f"Error or not transaction for block range {current_block} - {next_block}")
              break
        all_transactions.extend(formatted_transactions)
        # print(f"Fetched {len(formatted_transactions)} txs from blocks {current_block} to {next_block}")
        logging.info(f"Fetched {len(formatted_transactions)} txs from blocks {current_block} to {next_block}")
        current_block = next_block + 1
        time.sleep(delay)
    print(f"COMPLETED")
    return all_transactions

@app.route("/",methods = ["GET", "POST"])
def index():
    transactions = []
    address = ""
    start_block = ""

    if request.method == "POST":
        address = request.form["address"]
        start_block = request.form["start_block"]
        transactions = get_all_transaction(address,int(start_block))

    return render_template("index.html", transactions = transactions,address = address, start_block = start_block)


ETHERSCAN_API_KEY = os.getenv('ETHERSCAN_API_KEY')
QUICKNODE_URL = f"https://tiniest-quaint-mansion.quiknode.pro/{QUICKNODE_ENDPOINT_API_KEY}" 
w3 = Web3(Web3.HTTPProvider(QUICKNODE_URL))

def get_block_by_timestamp(timestamp):
    url = 'https://api.etherscan.io/api'
    params = {
        'module': 'block',
        'action': 'getblocknobytime',
        'timestamp': timestamp,
        'closest': 'before',
        'apikey': ETHERSCAN_API_KEY
    }
    resp = requests.get(url, params=params)
    data = resp.json()
    if data['status'] == '1':
        return int(data['result'])
    return None

TOKENS = {
    "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
    "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "DAI":  "0x6B175474E89094C44Da98b954EedeAC495271d0F",
    "WBTC": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
    "LINK": "0x514910771AF9Ca656af840dff83E8264EcF986CA",
    "UNI":  "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",
    "AAVE": "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9",
    "COMP": "0xc00e94Cb662C3520282E6f5717214004A7f26888",
}
ERC20_ABI = json.loads("""[
    {
        "constant":true,
        "inputs":[{"name":"_owner","type":"address"}],
        "name":"balanceOf",
        "outputs":[{"name":"balance","type":"uint256"}],
        "type":"function"
    },
    {
        "constant":true,
        "inputs":[],
        "name":"decimals",
        "outputs":[{"name":"","type":"uint8"}],
        "type":"function"
    },
    {
        "constant":true,
        "inputs":[],
        "name":"symbol",
        "outputs":[{"name":"","type":"string"}],
        "type":"function"
    }
]""")
def get_token_balances(address, block_number):
    balances = {}
    checksum_address = Web3.to_checksum_address(address)

    for token_name, token_address in TOKENS.items():
        try:
            token_contract = w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=ERC20_ABI)
            balance = token_contract.functions.balanceOf(checksum_address).call(block_identifier=block_number)
            decimals = token_contract.functions.decimals().call()
            symbol = token_contract.functions.symbol().call()
            human_balance = balance / (10 ** decimals)
            if human_balance > 0:
                balances[symbol] = human_balance

        except Exception as e:
            # print(f"Error while fetching token {token_name}: {e}")
            logging.error(f"Error while fetching token {token_name}: {e}")
    return balances

@app.route('/balance', methods=['GET', 'POST'])
def balance():
    balance_eth=None
    token_balances = {}
    error = None

    if request.method == 'POST':
        address = request.form.get('address')
        date_str = request.form.get('date')

        if not w3.is_address(address):
            error = "Invalid Ethereum address."
        else:
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                timestamp = int(dt.timestamp())

                block_number = get_block_by_timestamp(timestamp)
                if block_number is None:
                    error = "Unable to find a block for the specified date."
                else:
                    balance_wei = w3.eth.get_balance(address, block_identifier=block_number)
                    balance_eth = balance_wei / 10**18
                    token_balances = get_token_balances(address, block_number)
            except Exception as e:
                error = f"Error: {str(e)}"

    return render_template('balance.html', balance_eth=balance_eth, token_balances=token_balances, error=error)

if __name__ == "__main__":
    app.run(debug = False)
