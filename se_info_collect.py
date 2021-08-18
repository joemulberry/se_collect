

import requests
import json
import time

url = 'https://raw.githubusercontent.com/joemulberry/para_baseinfo/main/core.json'
resp = requests.get(url)
data = json.loads(resp.text)


url = 'https://raw.githubusercontent.com/joemulberry/parallel/main/data/opensea_parallel_dumps.json'
resp = requests.get(url)
os_data = json.loads(resp.text)


ses = []
for d in data:
    if d['standard'] == 'se':
        ses.append(d)

ids = [(x['parallel_id'], x['opensea_id'], x['supply'], ) for x in ses]

dicts = []

for se in ses:
    time.sleep(1)
    url = "https://api.opensea.io/wyvern/v1/orders"
    querystring = {"asset_contract_address": "0x76be3b62873462d2142405439777e971754e8e77", "bundled": "false", "include_bundled": "false", "include_invalid": "false", "token_ids": se['opensea_id'], "limit": "50", "offset": "0", "order_by": "created_date", "order_direction": "desc"}
    headers = {"Accept": "application/json"}
    response = requests.request("GET", url, headers=headers, params=querystring)
    orderdata = response.json()
    if len(orderdata.keys()) == 1:
        print(orderdata)
    print(orderdata.keys())
    orders = orderdata['orders']

    # Get the sales dict from OS data 
    for d in os_data:
        if d['token_id'] == se['opensea_id']:
            break

    if d['last_sale'] != None:
        token_id = d['last_sale']['asset']['token_id']
        currency = d['last_sale']['payment_token']['symbol']
        usd_rate = float(d['last_sale']['payment_token']['usd_price'])
        eth_rate = float(d['last_sale']['payment_token']['eth_price'])
        decimals = int(d['last_sale']['payment_token']['decimals'])
        event_timestamp = d['last_sale']['event_timestamp']

        total_price = d['last_sale']['total_price']
        quantity = int(d['last_sale']['quantity'])
        total_price = float(total_price[:len(total_price)-decimals] + '.' + total_price[len(total_price)-decimals:])

        eth_price = total_price * eth_rate
        eth_price = eth_price / quantity
        usd_price = eth_price * usd_rate

        last_sale_d = {'currency': currency,
            'event_timestamp': event_timestamp,
            'eth_price': eth_price,
            'usd_price': usd_price}

    else:
        last_sale_d = {'currency': None,
                        'event_timestamp': None,
                        'eth_price': None,
                        'usd_price': None}
                        
    bids = []
    asks = []

    for order in orders:
        base_price = order['base_price']
        decimals = int(order['payment_token_contract']['decimals'])
        eth_price = float(order['payment_token_contract']['eth_price'])
        currency = order['payment_token_contract']['symbol']
        quantity = int(order['quantity'])
        side = order['side']

        base_price = float(base_price[:len(base_price)-decimals] +
                            '.' + base_price[len(base_price)-decimals:])
        base_price = (base_price * eth_price) / quantity

        if last_sale_d['eth_price'] != None:
            pct_diff_from_last_sale = (base_price - last_sale_d['eth_price']) / base_price 
        else:
            pct_diff_from_last_sale = None
            
        if currency != "DAI":
            if side == 0:
                bids.append(base_price)
            else:
                asks.append(base_price)
                
    print(len(bids), 'bids')
    print(len(asks), 'asks')
    
    number_of_bids = len(bids)
    number_of_asks = len(asks)
    
    if number_of_bids >0:
        highest_bid = round(max(bids), 3)
    else:
        highest_bid = None
        
    if number_of_asks > 0:
        lowest_ask = round(max(asks), 3)
    else:
        lowest_ask = None

    if lowest_ask != None and highest_bid != None:
        market_gap = round(lowest_ask - highest_bid, 3)
    else:
        market_gap = None

    if last_sale_d['eth_price'] != None:
        market_cap = se['supply'] * last_sale_d['eth_price']
    else:
        if highest_bid != None:
            market_cap = se['supply'] * highest_bid
        elif lowest_ask != None:
            market_cap = se['supply'] * lowest_ask
        else:
            market_cap = None


    overview = {'parallel_id': se['parallel_id'],
                'opensea_id': se['opensea_id'],
                'parallel': se['parallel'],
                'name': se['name'],
                'total_sales': d['num_sales'],
                'number_of_bids': len(bids),
                'number_of_asks': len(asks),
                'lowest_ask': lowest_ask,
                'highest_bid': highest_bid,
                'pct_on_sale': round(len(asks) / se['supply'], 3),
                'last_sale_price': last_sale_d['eth_price'],
                'market_gap': market_gap,
                'market_cap': market_cap,
                'pct_diff_from_last_sale': pct_diff_from_last_sale,
                'last_sale': last_sale_d}

    if 'recon' in overview['name']:
        print(overview)
    dicts.append(overview)


paras = []

count_array = [0,0,0,0,0,0]
para_array = ['augencore', 'earthen', 'kathari', 'marcolian', 'shroud', 'universal']

for dd in dicts:
    
    if dd['market_cap'] != None:
        count_array[para_array.index(dd['parallel'])] += dd['market_cap']

    paras.append(dd['parallel'])

# print(list(set(paras)))


# for p,c in zip(para_array, count_array):
#     print(p,c)
