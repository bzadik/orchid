import logging
import os
import requests
from web3 import Web3

def get_usd_per_x_coinbase(token_sym) -> float:
    r = requests.get(url="https://api.coinbase.com/v2/prices/" + token_sym + "-USD/spot")
    data = r.json()
    logging.debug(data)
    usd_per_x = float(0.0);
    if ('data' in data):
        usd_per_x = float(data['data']['amount'])
    else:
        logging.debug(f"invalid token or not found: {token_sym}")
    logging.debug(f"usd_per_x_coinbase {token_sym}: {usd_per_eth}")
    return usd_per_x

# example: OXT ETH BTC DAI BNB AVAX
def get_usd_per_x_binance(token_sym) -> float:
    r = requests.get(url="https://api.binance.com/api/v3/avgPrice?symbol=" + token_sym + "USDT")
    data = r.json()
    logging.debug(data)
    usd_per_x = float(0.0);
    if ('price' in data):
        usd_per_x = float(data['price'])
    else:
        logging.debug(f"invalid token or not found: {token_sym}")
    logging.debug(f"usd_per_x_binance {token_sym}: {usd_per_eth}")
    return usd_per_x

def get_txn_cost_wei(txn):
    value_wei    = txn['value']
    gas          = txn['gas']
    gasPrice     = txn['gasPrice']
    gascost_wei  = gas*gasPrice
    cost_wei     = value_wei + gascost_wei
    return cost_wei

wei_per_eth = 1000000000000000000

def get_txn_cost_usd(txn):
    cost_wei  = get_txn_cost_wei(txn)
    cost_eth  = cost_wei / wei_per_eth
    cost_usd  = cost_eth * usd_per_eth
    return cost_usd

def sendRaw_wei_(web3_websock,txn,  pubkey,privkey,nonce,max_cost_wei):

    cost_wei     = get_txn_cost_wei(txn)
    if (cost_wei > max_cost_wei):
        logging.debug(f'sign_send_Transaction cost_wei({cost_wei}) > max_cost_wei({max_cost_wei})')
        return None,0.0

    w3       = Web3(Web3.WebsocketProvider(web3_websock, websocket_timeout=900))

    txn['from']  = pubkey
    txn['nonce'] = nonce

    txn_signed = w3.eth.account.sign_transaction(txn, private_key=privkey,)
    logging.debug(f'sign_send_Transaction txn_signed: {txn_signed}')

    txn_hash = w3.eth.sendRawTransaction(txn_signed.rawTransaction)
    logging.debug(f'sign_send_Transaction submitted transaction with hash: {txn_hash.hex()}')
    return txn_hash.hex(),cost_wei


def sendRaw_usd_(web3_websock,txn, pubkey,privkey,nonce,max_cost_usd):

    usd_per_eth = get_usd_per_x_coinbase('ETH')
    if (usd_per_eth == 0.0):
        usd_per_eth = get_usd_per_x_binance('ETH')

    max_cost_eth = max_cost_usd / usd_per_eth
    max_cost_wei = max_cost_eth * wei_per_eth

    txnhash,cost_wei = sendRaw_wei_(web3_websock,txn, pubkey,privkey,nonce,max_cost_wei)

    cost_eth = cost_wei / wei_per_eth
    cost_usd = cost_eth * usd_per_eth

    return txnhash,cost_usd


def sendRaw(web3_websock,txn,receiptHash):

    #todo: make fully idempotent, get the transaction hash and look it up?

    max_cost_usd     = get_account_balance(receiptHash)
    pubkey,privkey   = get_executor_account()
    nonce            = get_nonce(pubkey)

    txnhash,cost_usd = sendRaw_usd_(web3_websock,txn, pubkey,privkey,nonce,max_cost_usd)

    if (txnhash != None):
        save_transaction(txnhash, txn)
        debit_account_balance(receiptHash, cost_usd)

    return txnhash


def has_transaction_failed(web3_websock,txnhash,txn):

    w3 = Web3(Web3.WebsocketProvider(web3_websock, websocket_timeout=900))
    success     = True
    txn_receipt = None
    try:
        txn_receipt = w3.eth.getTransactionReceipt(txnhash)
        success     = Bool(txn_receipt['status'])
    except (Web3.exceptions.TransactionNotFound, TransactionNotFound):
        txn_receipt = None

    pubkey     = txn['from']
    txn_nonce  = txn['nonce']
    cur_nonce  = get_nonce(pubkey)

    result = (success == False) or ((txn_receipt == None) and (cur_nonce > txn_nonce))

    return result



def refund_failed_txn(web3_websock,txnhash,receiptHash):

    txn = load_transaction(txnhash)

    if (has_transaction_failed(web3_websock,txn) == False):
        return "error: transaction {} is still pending"

    cost_usd = get_txn_cost_usd(txn)
    credit_account_balance(receiptHash, cost_usd)

    return "success"


'''
def build_sign_send_Transaction(web3_websock,contract_addr,func_name,args,value,gas,gasprice,  pubkey,privkey,nonce,max_cost_usd):
    #w3       = Web3(Web3.WebsocketProvider(os.environ['WEB3_WEBSOCKET'], websocket_timeout=900))
    w3       = Web3(Web3.WebsocketProvider(web3_websock, websocket_timeout=900))
    contract = w3.eth.contract( abi=get_contract_abi(contract_addr), address=contract_addr, )
    #method   = getattr(contract.functions, func_name)
    method   = contract.get_function_by_name(func_name)

    txn = method(**args).buildTransaction(
        {
            'chainId': 1,
            'from': pubkey,
            'gas': gas,
            'gasPrice': gasprice,
            'nonce': nonce,
        }
    )
    logging.debug(f'build_sign_send_Transaction txn: {txn}')

    txn_signed = w3.eth.account.sign_transaction(txn, private_key=privkey,)
    logging.debug(f'build_sign_send_Transaction txn_signed: {txn_signed}')

    txn_hash = w3.eth.sendRawTransaction(txn_signed.rawTransaction)
    logging.debug(f'build_sign_send_Transaction submitted transaction with hash: {txn_hash.hex()}')
    return txn_hash.hex()
'''