import json
import time
import websocket
import pandas as pd
assets = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
assets = [coin.lower() + '@kline_1m' for coin in assets]
assets = '/'.join(assets)


def on_message(ws, message):
    message = json.loads(message)
    manipulation(message)
    

def manipulation(source):
    """
    timeout_in_seconds = 5
    start = end = time.time()
    while (end - start < timeout_in_seconds):
        end = time.time()
    """
    
    rel_data = source['data']['k']['c']
    event_time = pd.to_datetime(source['data']['E'], unit='ms')
    df = pd.DataFrame(rel_data, columns=[source['data']['s']], index = [event_time])
    df.index.name ='timestamp'
    df = df.astype(float)
    df = df.reset_index()
    print(df)
    return df

socket = "wss://stream.binance.com:9443/stream?streams=" + assets

ws = websocket.WebSocketApp(socket, on_message=on_message)
ws.run_forever()
