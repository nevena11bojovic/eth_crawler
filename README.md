# Ethereum Transaction Crawler

## Description

A simple web application that allows users to input an Ethereum wallet address and a starting block number, then view all ETH transactions involving that wallet from the given block to the latest.

## Tech Stack
- Python
- Flask
- Etherscan API
- QuickNode API

## Setup
 
1. Clone the repository:
```bash
git clone https://github.com/nevena11bojovic/eth_crawler.git
cd "ethereum transactions crawler"
```

2. Create a `.env` file with your Etherscan API key:
```
ETHERSCAN_API_KEY=your_api_key
QUICKNODE_ENDPOINT_API_KEY = your_api_key
```

3. Install dependencies:
```bash
pip install -r requirements.txt
pip install Flask web3 python-dotenv
```

4. Run the app:
```bash
flask run
```

5. Open `http://localhost:5000` in your browser.
   Open `http://localhost:5000/balance` in your browser.


## Author
Nevena Bojović
