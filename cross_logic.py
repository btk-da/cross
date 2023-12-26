# -*- coding: utf-8 -*-
"""
Created on Fri Sep  8 17:09:12 2023

@author: gorka
"""

#LOGIC

import socket
import time
import requests
import pickle
import copy
from binance.exceptions import BinanceAPIException
from bot_symbol_combi import Symbol_combi
from bot_symbol_long import Symbol_long
from bot_symbol_short import Symbol_short
from bot_notifier import Notifier
from bot_account import Margin_account
from bot_database import init_database, sql_session
from sqlalchemy import delete
from sqlalchemy.exc import OperationalError


url = 'https://api.telegram.org/bot6332743294:AAFKcqzyfKzXAPSGhR6eTKLPMyx0tpCzeA4/sendMessage'

inputs = [{'drop': 1.25, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.25, 'sell_trail':0.15, 'level':0.5, 'pond':5, 'asset': 'BTC'},
          {'drop': -1.25, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.25, 'sell_trail':0.15, 'level':0.5, 'pond':5, 'asset': 'BTC'},
          {'drop': 1.25, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.25, 'sell_trail':0.15, 'level':0.5, 'pond':5, 'asset': 'ETH'},
          {'drop': -1.25, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.25, 'sell_trail':0.15, 'level':0.5, 'pond':5, 'asset': 'ETH'},
          {'drop': 1.25, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.25, 'sell_trail':0.15, 'level':0.5, 'pond':5, 'asset': 'BNB'},
          {'drop': -1.25, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.25, 'sell_trail':0.15, 'level':0.5, 'pond':5, 'asset': 'BNB'},
          {'drop': 1.25, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.25, 'sell_trail':0.15, 'level':0.5, 'pond':5, 'asset': 'ADA'},
          {'drop': -1.25, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.25, 'sell_trail':0.15, 'level':0.5, 'pond':5, 'asset': 'ADA'},
          {'drop': 1.25, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.25, 'sell_trail':0.15, 'level':0.5, 'pond':5, 'asset': 'ATOM'},
          {'drop': -1.25, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.25, 'sell_trail':0.15, 'level':0.5, 'pond':5, 'asset': 'ATOM'},
          {'drop': 1.25, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.25, 'sell_trail':0.15, 'level':0.5, 'pond':5, 'asset': 'SOL'},
          {'drop': -1.25, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.25, 'sell_trail':0.15, 'level':0.5, 'pond':5, 'asset': 'SOL'},
          {'drop': 1.25, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.25, 'sell_trail':0.15, 'level':0.5, 'pond':5, 'asset': 'XRP'},
          {'drop': -1.25, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.25, 'sell_trail':0.15, 'level':0.5, 'pond':5, 'asset': 'XRP'},
          {'drop': 1.25, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.25, 'sell_trail':0.15, 'level':0.5, 'pond':5, 'asset': 'DOGE'},
          {'drop': -1.25, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.25, 'sell_trail':0.15, 'level':0.5, 'pond':5, 'asset': 'DOGE'},
          {'drop': 1.25, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.25, 'sell_trail':0.15, 'level':0.5, 'pond':5, 'asset': 'TRX'},
          {'drop': -1.25, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.25, 'sell_trail':0.15, 'level':0.5, 'pond':5, 'asset': 'TRX'},
          {'drop': 1.25, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.25, 'sell_trail':0.15, 'level':0.5, 'pond':5, 'asset': 'DOT'},
          {'drop': -1.25, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.25, 'sell_trail':0.15, 'level':0.5, 'pond':5, 'asset': 'DOT'},
          {'drop': 1.25, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.25, 'sell_trail':0.15, 'level':0.5, 'pond':5, 'asset': 'EOS'},
          {'drop': -1.25, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.25, 'sell_trail':0.15, 'level':0.5, 'pond':5, 'asset': 'EOS'},
          {'drop': 1.25, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.25, 'sell_trail':0.15, 'level':0.5, 'pond':5, 'asset': 'LTC'},
          {'drop': -1.25, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.25, 'sell_trail':0.15, 'level':0.5, 'pond':5, 'asset': 'LTC'},
          {'drop': 1.25, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.25, 'sell_trail':0.15, 'level':0.5, 'pond':5, 'asset': 'BCH'},
          {'drop': -1.25, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.25, 'sell_trail':0.15, 'level':0.5, 'pond':5, 'asset': 'BCH'},
          {'drop': 1.25, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.25, 'sell_trail':0.15, 'level':0.5, 'pond':5, 'asset': 'LINK'},
          {'drop': -1.25, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.25, 'sell_trail':0.15, 'level':0.5, 'pond':5, 'asset': 'LINK'},
          {'drop': 1.25, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.25, 'sell_trail':0.15, 'level':0.5, 'pond':5, 'asset': 'SHIB'},
          {'drop': -1.25, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.25, 'sell_trail':0.15, 'level':0.5, 'pond':5, 'asset': 'SHIB'},
          {'drop': 1.25, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.25, 'sell_trail':0.15, 'level':0.5, 'pond':5, 'asset': 'AVAX'},
          {'drop': -1.25, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.25, 'sell_trail':0.15, 'level':0.5, 'pond':5, 'asset': 'AVAX'},
          {'drop': 1.25, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.25, 'sell_trail':0.15, 'level':0.5, 'pond':5, 'asset': 'XLM'},
          {'drop': -1.25, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.25, 'sell_trail':0.15, 'level':0.5, 'pond':5, 'asset': 'XLM'},
          {'drop': 1.25, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.25, 'sell_trail':0.15, 'level':0.5, 'pond':5, 'asset': 'UNI'},
          {'drop': -1.25, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.25, 'sell_trail':0.15, 'level':0.5, 'pond':5, 'asset': 'UNI'},
          {'drop': 1.25, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.25, 'sell_trail':0.15, 'level':0.5, 'pond':5, 'asset': 'ETC'},
          {'drop': -1.25, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.25, 'sell_trail':0.15, 'level':0.5, 'pond':5, 'asset': 'ETC'},
          {'drop': 1.25, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.25, 'sell_trail':0.15, 'level':0.5, 'pond':5, 'asset': 'FIL'},
          {'drop': -1.25, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.25, 'sell_trail':0.15, 'level':0.5, 'pond':5, 'asset': 'FIL'},
          {'drop': 1.25, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.25, 'sell_trail':0.15, 'level':0.5, 'pond':5, 'asset': 'HBAR'},
          {'drop': -1.25, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.25, 'sell_trail':0.15, 'level':0.5, 'pond':5, 'asset': 'HBAR'},
          {'drop': 1.25, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.25, 'sell_trail':0.15, 'level':0.5, 'pond':5, 'asset': 'VET'},
          {'drop': -1.25, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.25, 'sell_trail':0.15, 'level':0.5, 'pond':5, 'asset': 'VET'},
          {'drop': 1.25, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.25, 'sell_trail':0.15, 'level':0.5, 'pond':5, 'asset': 'NEAR'},
          {'drop': -1.25, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.25, 'sell_trail':0.15, 'level':0.5, 'pond':5, 'asset': 'NEAR'},
          {'drop': 1.25, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.25, 'sell_trail':0.15, 'level':0.5, 'pond':5, 'asset': 'GRT'},
          {'drop': -1.25, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.25, 'sell_trail':0.15, 'level':0.5, 'pond':5, 'asset': 'GRT'},
          {'drop': 1.25, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.25, 'sell_trail':0.15, 'level':0.5, 'pond':5, 'asset': 'AAVE'},
          {'drop': -1.25, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.25, 'sell_trail':0.15, 'level':0.5, 'pond':5, 'asset': 'AAVE'},
          {'drop': 1.25, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.25, 'sell_trail':0.15, 'level':0.5, 'pond':5, 'asset': 'DASH'},
          {'drop': -1.25, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.25, 'sell_trail':0.15, 'level':0.5, 'pond':5, 'asset': 'DASH'},
          {'drop': 1.25, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.25, 'sell_trail':0.15, 'level':0.5, 'pond':5, 'asset': 'MATIC'},
          {'drop': -1.25, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.25, 'sell_trail':0.15, 'level':0.5, 'pond':5, 'asset': 'MATIC'},
          {'drop': 1.25, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.25, 'sell_trail':0.15, 'level':0.5, 'pond':5, 'asset': 'ICP'},
          {'drop': -1.25, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.25, 'sell_trail':0.15, 'level':0.5, 'pond':5, 'asset': 'ICP'},
          {'drop': 1.25, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.25, 'sell_trail':0.15, 'level':0.5, 'pond':5, 'asset': 'RUNE'},
          {'drop': -1.25, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.25, 'sell_trail':0.15, 'level':0.5, 'pond':5, 'asset': 'RUNE'},
          {'drop': 1.25, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.25, 'sell_trail':0.15, 'level':0.5, 'pond':5, 'asset': 'IMX'},
          {'drop': -1.25, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.25, 'sell_trail':0.15, 'level':0.5, 'pond':5, 'asset': 'IMX'}]


assets = []
for i in inputs:
    assets.append(i['asset'])
assets = set(assets)

backup = False

if __name__ == '__main__':
    
    if backup:
        account = Margin_account(Notifier())
        master = Symbol_combi()
        master.account = account
        sql_tables = init_database(assets, True)
        master.account.notifier.tables = sql_tables
        
        with open("symbols.pickle", "rb") as f:
            symbols_backup = pickle.load(f)
        
        inputs = []
        for i in symbols_backup.keys():
            inputs.append(symbols_backup[i]['params'])
            
        master.add_symbols(inputs)
        master.init_params(True)
            
        for name, data in symbols_backup.items():
            for symbol_instance in master.symbol_list:
                if symbol_instance.name == name:
                    for attr, value in data.items():
                        setattr(symbol_instance, attr, value)   
                    symbol_instance.master = master
                    master.account.notifier.register_output('Info', 'general', 'general', symbol_instance.name + 'charged')        
        
        master.account.notifier.register_output('Info', 'general', 'general', 'Backup Charged')
        print('Backup charged')
        
    else:
        account = Margin_account(Notifier())
        master = Symbol_combi()
        master.account = account
        sql_tables = init_database(assets, False)
        master.account.notifier.tables = sql_tables
        master.add_symbols(inputs)
        master.init_params(False)  
        master.account.notifier.register_output('Info', 'general', 'general', 'System initialized')
        print('System initialized')
    
    print('Start Operating')
    
    
    while True:
        
        if master.engine_working == True:
        
            try:
                master.update_open_tr()
                
                symbols_backup = {}
                for symbol in master.symbol_list:
                    symbols_backup[symbol.name] = copy.deepcopy(symbol.__dict__)
                    symbols_backup[symbol.name]['master'] = []
    
                with open("symbols.pickle", "wb") as f:
                    pickle.dump(symbols_backup, f)
                
            except BinanceAPIException as e:
                master.account.notifier.send_error('General', f'Binance API error: {e}; Tipo: {type(e)}; Args: {e.args}; Linea: {e.__traceback__.tb_lineno}')
            except requests.exceptions.ReadTimeout as e:
                master.account.notifier.send_error('General', f"Error de tiempo de espera en la API de Binance: {e}")
            except OperationalError as e:
                master.account.notifier.send_error('General', f"Error de conexión a la base de datos: {e}")
            except Exception as e:
                master.account.notifier.send_error('General', f'ERROR NO IDENTIFICADO: {e}; Tipo: {type(e)}; Args: {e.args}; Linea: {e.__traceback__.tb_lineno}')
            time.sleep(30)
            
            try: # Conectarse con frontend y pedir instrucciones
                logic_front_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                logic_front_socket.settimeout(5) # Esperar 5 segundos antes de ejecutar la lógica
                logic_front_socket.connect(('localhost', 5559))
                
                texto = 'Conexion success'
                mensaje = texto.encode('utf-8')
                logic_front_socket.send(mensaje)
                
                requests.post(url, data={'chat_id': '-1001802125737', 'text':  texto, 'parse_mode': 'HTML'})
                
                logic_front_socket.close()
                
                master.engine_working = False
                requests.post(url, data={'chat_id': '-1001802125737', 'text':  'Engine stopped', 'parse_mode': 'HTML'})

            except socket.error as e:
                pass                
            except socket.timeout:
                pass

            except Exception as e:
                print('Error de logic al conectar frontend: ', str(e))
                requests.post(url, data={'chat_id': '-1001802125737', 'text':  'Error de logic al conectar frontend: ' + str(e), 'parse_mode': 'HTML'})
                master.account.notifier.send_error('General', 'Error de logic al conectar frontend: ', str(e))
            finally:
                logic_front_socket.close()

        elif master.engine_working == False:
            
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as front_server:
                front_server.bind(('localhost', 5558))
                front_server.listen(1)
                conexion, direccion = front_server.accept()
                
                try:
                    data = conexion.recv(1024)
                    texto = data.decode('utf-8')
                    requests.post(url, data={'chat_id': '-1001802125737', 'text':  'Text received: ' + texto, 'parse_mode': 'HTML'})
                    time.sleep(2)
                
                    if 'SWITCH' in texto:
                        switch_data = conexion.recv(4096)
                        switch_params = pickle.loads(switch_data)
                        requests.post(url, data={'chat_id': '-1001802125737', 'text': 'Side: ' + switch_params['side'] + ' Mode: ' + switch_params['mode'], 'parse_mode': 'HTML'})
                        
                        with open("symbols.pickle", "rb") as f:
                            symbols_backup = pickle.load(f)
                            
                        for name, data in symbols_backup.items():
                            for symbol_instance in master.symbol_list:
                                if symbol_instance.name == name:
                                    for attr, value in data.items():
                                        setattr(symbol_instance, attr, value)
                                    symbol_instance.master = master
                                    
                        if switch_params['side'] == 'All':
                            if switch_params['mode'] == 'OFF':
                                for i in master.symbol_list:
                                    i.switch = False
                                    requests.post(url, data={'chat_id': '-1001802125737', 'text':  i.name + 'turned  ' + str(i.switch), 'parse_mode': 'HTML'})
                            elif switch_params['mode'] == 'ON':
                                for i in master.symbol_list:
                                    i.switch = True
                                    requests.post(url, data={'chat_id': '-1001802125737', 'text':  i.name + 'turned  ' + str(i.switch), 'parse_mode': 'HTML'})
                                    
                        elif switch_params['side'] == 'Long':
                            if switch_params['mode'] == 'OFF':
                                for i in master.symbol_list:
                                    if i.side == 'Long':
                                        i.switch = False
                                        requests.post(url, data={'chat_id': '-1001802125737', 'text':  i.name + 'turned  ' + str(i.switch), 'parse_mode': 'HTML'})

                            elif switch_params['mode'] == 'ON':
                                for i in master.symbol_list:
                                    if i.side == 'Long':
                                        i.switch = True
                                        requests.post(url, data={'chat_id': '-1001802125737', 'text':  i.name + 'turned  ' + str(i.switch), 'parse_mode': 'HTML'})

                        elif switch_params['side'] == 'Short':
                            if switch_params['mode'] == 'OFF':
                                for i in master.symbol_list:
                                    if i.side == 'Short':
                                        i.switch = False
                                        requests.post(url, data={'chat_id': '-1001802125737', 'text':  i.name + 'turned  ' + str(i.switch), 'parse_mode': 'HTML'})

                            elif switch_params['mode'] == 'ON':
                                for i in master.symbol_list:
                                    if i.side == 'Short':
                                        i.switch = True
                                        requests.post(url, data={'chat_id': '-1001802125737', 'text':  i.name + 'turned  ' + str(i.switch), 'parse_mode': 'HTML'})

                        restart_symbols = delete(master.account.notifier.tables['symbols'])
                        sql_session.execute(restart_symbols)
                        for symbol in master.symbol_list:
                            new_row = master.account.notifier.tables['symbols'](Name=symbol.name, Drop=symbol.drop, Profit=symbol.profit, K=symbol.k, Buy_trail=symbol.buy_trail, Sell_trail=symbol.sell_trail, Level=symbol.level, Pond=symbol.pond, Switch=symbol.switch, Symbol_status=symbol.symbol_status, Can_open=symbol.can_open, Can_average=symbol.can_average, Can_close=symbol.can_close, Can_open_trail=symbol.can_open_trail, Can_average_trail=symbol.can_average_trail, Can_close_trail=symbol.can_close_trail)
                            sql_session.add(new_row)
                        sql_session.commit()
    
                        master.engine_working = True
                        requests.post(url, data={'chat_id': '-1001802125737', 'text': 'Engine started (switch)', 'parse_mode': 'HTML'})
                        conexion.close()
    
                    elif 'EDIT SYMBOL' in texto:
                        edit_symbol_data = conexion.recv(4096)
                        edit_params = pickle.loads(edit_symbol_data)
                        requests.post(url, data={'chat_id': '-1001802125737', 'text': 'Name: ' + edit_params['name'] + ' Attribute: ' + edit_params['attribute'] + ' Value: ' + str(edit_params['value']), 'parse_mode': 'HTML'})
                        
                        with open("symbols.pickle", "rb") as f:
                            symbols_backup = pickle.load(f)
                            
                        for name, data in symbols_backup.items():
                            for symbol_instance in master.symbol_list:
                                if symbol_instance.name == name:
                                    for attr, value in data.items():
                                        setattr(symbol_instance, attr, value)
                                    symbol_instance.master = master
                                    
                        mapeo = {'Drop': 'drop', 'TP': 'profit', 'K': 'k', 'Buy Trail': 'buy_trail', 'Sell Trail': 'sell_trail', 'Level': 'level', 'Pond': 'pond',
                                    'Switch': 'switch', 'Symbol Status': 'symbol status', 'Can Open': 'can_open', 'Can Average': 'can_average', 'Can Close': 'can_close', 
                                    'Can Open Trail': 'can_open_trail', 'Can Average Trail': 'can_average_trail', 'Can Close Trail': 'can_close_trail'}
                        
                        if edit_params['attribute'] in mapeo:
                            attribute_name = mapeo[edit_params['attribute']]
                                    
                        if edit_params['name'] == 'All':
                            
                            for selected_symbol in master.symbol_list:
                                if attribute_name in ['switch', 'symbol status', 'can_open', 'can_average', 'can_close', 'can_open_trail', 'can_average_trail', 'can_close_trail']:
                                    setattr(selected_symbol, attribute_name, bool(int(edit_params['value'])))
                                else:
                                    setattr(selected_symbol, attribute_name, edit_params['value'])
                                warn = 'Changed completed ' + 'Symbol: ' + symbol.name + 'Param: ' + str(edit_params['attribute']) + 'New Value: ' + str(edit_params['value'])
                                requests.post(url, data={'chat_id': '-1001802125737', 'text': warn, 'parse_mode': 'HTML'})
                                
                        else:                               

                            selected_symbol = next(symbol for symbol in master.symbol_list if symbol.name == edit_params['name'])
                            # mapeo = {'Drop': 'drop', 'TP': 'profit', 'K': 'k', 'Buy Trail': 'buy_trail', 'Sell Trail': 'sell_trail', 'Level': 'level', 'Pond': 'pond',
                            #             'Switch': 'switch', 'Symbol Status': 'symbol status', 'Can Open': 'can_open', 'Can Average': 'can_average', 'Can Close': 'can_close', 
                            #             'Can Open Trail': 'can_open_trail', 'Can Average Trail': 'can_average_trail', 'Can Close Trail': 'can_close_trail'}
                            
                            # if edit_params['attribute'] in mapeo:
                                # attribute_name = mapeo[edit_params['attribute']]
                            if attribute_name in ['switch', 'symbol status', 'can_open', 'can_average', 'can_close', 'can_open_trail', 'can_average_trail', 'can_close_trail']:
                                setattr(selected_symbol, attribute_name, bool(int(edit_params['value'])))
                            else:
                                setattr(selected_symbol, attribute_name, edit_params['value'])
                    
                            warn = 'Changed completed ' + 'Symbol: ' + selected_symbol.name + 'Param: ' + str(attribute_name) + 'New Value: ' + str(edit_params['value'])
                            requests.post(url, data={'chat_id': '-1001802125737', 'text': warn, 'parse_mode': 'HTML'})

                        restart_symbols = delete(master.account.notifier.tables['symbols'])
                        sql_session.execute(restart_symbols)
                        for symbol in master.symbol_list:
                            symbol.trading_points()
                            new_row = master.account.notifier.tables['symbols'](Name=symbol.name, Drop=symbol.drop, Profit=symbol.profit, K=symbol.k, Buy_trail=symbol.buy_trail, Sell_trail=symbol.sell_trail, Level=symbol.level, Pond=symbol.pond, Switch=symbol.switch, Symbol_status=symbol.symbol_status, Can_open=symbol.can_open, Can_average=symbol.can_average, Can_close=symbol.can_close, Can_open_trail=symbol.can_open_trail, Can_average_trail=symbol.can_average_trail, Can_close_trail=symbol.can_close_trail)
                            sql_session.add(new_row)
                        sql_session.commit()                    
        
                        master.engine_working = True
                        requests.post(url, data={'chat_id': '-1001802125737', 'text':  'Engine started (edit)', 'parse_mode': 'HTML'})
                        conexion.close()
    
                    elif 'ADD SYMBOL' in texto:
                        add_symbol_data = conexion.recv(4096)
                        add_symbol_params = pickle.loads(add_symbol_data)
                        requests.post(url, data={'chat_id': '-1001802125737', 'text': 'Drop: ' + str(add_symbol_params[0]['drop']) + ' Profit: ' + str(add_symbol_params[0]['profit']) + ' K: ' + str(add_symbol_params[0]['k']), 'parse_mode': 'HTML'})
                        
                        with open("symbols.pickle", "rb") as f:
                            symbols_backup = pickle.load(f)
                            
                        for name, data in symbols_backup.items():
                            for symbol_instance in master.symbol_list:
                                if symbol_instance.name == name:
                                    for attr, value in data.items():
                                        setattr(symbol_instance, attr, value)
                                    symbol_instance.master = master

                        master.add_new_symbol(add_symbol_params)
    
                        restart_symbols = delete(master.account.notifier.tables['symbols'])
                        sql_session.execute(restart_symbols)
                        for symbol in master.symbol_list:
                            new_row = master.account.notifier.tables['symbols'](Name=symbol.name, Drop=symbol.drop, Profit=symbol.profit, K=symbol.k, Buy_trail=symbol.buy_trail, Sell_trail=symbol.sell_trail, Level=symbol.level, Pond=symbol.pond, Switch=symbol.switch, Symbol_status=symbol.symbol_status, Can_open=symbol.can_open, Can_average=symbol.can_average, Can_close=symbol.can_close, Can_open_trail=symbol.can_open_trail, Can_average_trail=symbol.can_average_trail, Can_close_trail=symbol.can_close_trail)
                            sql_session.add(new_row)
                        sql_session.commit()      
    
                        requests.post(url, data={'chat_id': '-1001802125737', 'text': 'New symbol added', 'parse_mode': 'HTML'})
                        master.engine_working = True
                        requests.post(url, data={'chat_id': '-1001802125737', 'text':  'Engine started (add)', 'parse_mode': 'HTML'})
                        conexion.close()

                except socket.error:
                    pass
                except socket.timeout:
                    pass
                
                finally:
                    conexion.close()