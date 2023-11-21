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
from bot_database import init_database, sql_assets, sql_session
from sqlalchemy import delete
from sqlalchemy.exc import OperationalError


url = 'https://api.telegram.org/bot6332743294:AAFKcqzyfKzXAPSGhR6eTKLPMyx0tpCzeA4/sendMessage'

inputs = [{'drop': 1, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.15, 'sell_trail':0.15, 'drop_param':2.5, 'level':3, 'pond':5, 'asset': 'BTC'},
          {'drop': -1, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.15, 'sell_trail':0.15, 'drop_param':2.5, 'level':3, 'pond':5, 'asset': 'BTC'},
          {'drop': 1, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.15, 'sell_trail':0.15, 'drop_param':2.5, 'level':3, 'pond':5, 'asset': 'ETH'},
          {'drop': -1, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.15, 'sell_trail':0.15, 'drop_param':2.5, 'level':3, 'pond':5, 'asset': 'ETH'},
          {'drop': 1, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.15, 'sell_trail':0.15, 'drop_param':2.5, 'level':3, 'pond':5, 'asset': 'BNB'},
          {'drop': -1, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.15, 'sell_trail':0.15, 'drop_param':2.5, 'level':3, 'pond':5, 'asset': 'BNB'},
          {'drop': 1, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.15, 'sell_trail':0.15, 'drop_param':2.5, 'level':3, 'pond':5, 'asset': 'ADA'},
          {'drop': -1, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.15, 'sell_trail':0.15, 'drop_param':2.5, 'level':3, 'pond':5, 'asset': 'ADA'},
          {'drop': 1, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.15, 'sell_trail':0.15, 'drop_param':2.5, 'level':3, 'pond':5, 'asset': 'ATOM'},
          {'drop': -1, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.15, 'sell_trail':0.15, 'drop_param':2.5, 'level':3, 'pond':5, 'asset': 'ATOM'},
          {'drop': 1, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.15, 'sell_trail':0.15, 'drop_param':2.5, 'level':3, 'pond':5, 'asset': 'SOL'},
          {'drop': -1, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.15, 'sell_trail':0.15, 'drop_param':2.5, 'level':3, 'pond':5, 'asset': 'SOL'},
          {'drop': 1, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.15, 'sell_trail':0.15, 'drop_param':2.5, 'level':3, 'pond':5, 'asset': 'XRP'},
          {'drop': -1, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.15, 'sell_trail':0.15, 'drop_param':2.5, 'level':3, 'pond':5, 'asset': 'XRP'},
          {'drop': 1, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.15, 'sell_trail':0.15, 'drop_param':2.5, 'level':3, 'pond':5, 'asset': 'DOGE'},
          {'drop': -1, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.15, 'sell_trail':0.15, 'drop_param':2.5, 'level':3, 'pond':5, 'asset': 'DOGE'},
          {'drop': 1, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.15, 'sell_trail':0.15, 'drop_param':2.5, 'level':3, 'pond':5, 'asset': 'TRX'},
          {'drop': -1, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.15, 'sell_trail':0.15, 'drop_param':2.5, 'level':3, 'pond':5, 'asset': 'TRX'},
          {'drop': 1, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.15, 'sell_trail':0.15, 'drop_param':2.5, 'level':3, 'pond':5, 'asset': 'DOT'},
          {'drop': -1, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.15, 'sell_trail':0.15, 'drop_param':2.5, 'level':3, 'pond':5, 'asset': 'DOT'},
          {'drop': 1, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.15, 'sell_trail':0.15, 'drop_param':2.5, 'level':3, 'pond':5, 'asset': 'EOS'},
          {'drop': -1, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.15, 'sell_trail':0.15, 'drop_param':2.5, 'level':3, 'pond':5, 'asset': 'EOS'},
          {'drop': 1, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.15, 'sell_trail':0.15, 'drop_param':2.5, 'level':3, 'pond':5, 'asset': 'LTC'},
          {'drop': -1, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.15, 'sell_trail':0.15, 'drop_param':2.5, 'level':3, 'pond':5, 'asset': 'LTC'},
          {'drop': 1, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.15, 'sell_trail':0.15, 'drop_param':2.5, 'level':3, 'pond':5, 'asset': 'BCH'},
          {'drop': -1, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.15, 'sell_trail':0.15, 'drop_param':2.5, 'level':3, 'pond':5, 'asset': 'BCH'},
          {'drop': 1, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.15, 'sell_trail':0.15, 'drop_param':2.5, 'level':3, 'pond':5, 'asset': 'LINK'},
          {'drop': -1, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.15, 'sell_trail':0.15, 'drop_param':2.5, 'level':3, 'pond':5, 'asset': 'LINK'},
          {'drop': 1, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.15, 'sell_trail':0.15, 'drop_param':2.5, 'level':3, 'pond':5, 'asset': 'SHIB'},
          {'drop': -1, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.15, 'sell_trail':0.15, 'drop_param':2.5, 'level':3, 'pond':5, 'asset': 'SHIB'},
          {'drop': 1, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.15, 'sell_trail':0.15, 'drop_param':2.5, 'level':3, 'pond':5, 'asset': 'AVAX'},
          {'drop': -1, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.15, 'sell_trail':0.15, 'drop_param':2.5, 'level':3, 'pond':5, 'asset': 'AVAX'},
          {'drop': 1, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.15, 'sell_trail':0.15, 'drop_param':2.5, 'level':3, 'pond':5, 'asset': 'XLM'},
          {'drop': -1, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.15, 'sell_trail':0.15, 'drop_param':2.5, 'level':3, 'pond':5, 'asset': 'XLM'},
          {'drop': 1, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.15, 'sell_trail':0.15, 'drop_param':2.5, 'level':3, 'pond':5, 'asset': 'UNI'},
          {'drop': -1, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.15, 'sell_trail':0.15, 'drop_param':2.5, 'level':3, 'pond':5, 'asset': 'UNI'},
          {'drop': 1, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.15, 'sell_trail':0.15, 'drop_param':2.5, 'level':3, 'pond':5, 'asset': 'ETC'},
          {'drop': -1, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.15, 'sell_trail':0.15, 'drop_param':2.5, 'level':3, 'pond':5, 'asset': 'ETC'},
          {'drop': 1, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.15, 'sell_trail':0.15, 'drop_param':2.5, 'level':3, 'pond':5, 'asset': 'FIL'},
          {'drop': -1, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.15, 'sell_trail':0.15, 'drop_param':2.5, 'level':3, 'pond':5, 'asset': 'FIL'},
          {'drop': 1, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.15, 'sell_trail':0.15, 'drop_param':2.5, 'level':3, 'pond':5, 'asset': 'HBAR'},
          {'drop': -1, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.15, 'sell_trail':0.15, 'drop_param':2.5, 'level':3, 'pond':5, 'asset': 'HBAR'},
          {'drop': 1, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.15, 'sell_trail':0.15, 'drop_param':2.5, 'level':3, 'pond':5, 'asset': 'VET'},
          {'drop': -1, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.15, 'sell_trail':0.15, 'drop_param':2.5, 'level':3, 'pond':5, 'asset': 'VET'},
          {'drop': 1, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.15, 'sell_trail':0.15, 'drop_param':2.5, 'level':3, 'pond':5, 'asset': 'NEAR'},
          {'drop': -1, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.15, 'sell_trail':0.15, 'drop_param':2.5, 'level':3, 'pond':5, 'asset': 'NEAR'},
          {'drop': 1, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.15, 'sell_trail':0.15, 'drop_param':2.5, 'level':3, 'pond':5, 'asset': 'GRT'},
          {'drop': -1, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.15, 'sell_trail':0.15, 'drop_param':2.5, 'level':3, 'pond':5, 'asset': 'GRT'},
          {'drop': 1, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.15, 'sell_trail':0.15, 'drop_param':2.5, 'level':3, 'pond':5, 'asset': 'AAVE'},
          {'drop': -1, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.15, 'sell_trail':0.15, 'drop_param':2.5, 'level':3, 'pond':5, 'asset': 'AAVE'},
          {'drop': 1, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.15, 'sell_trail':0.15, 'drop_param':2.5, 'level':3, 'pond':5, 'asset': 'DASH'},
          {'drop': -1, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.15, 'sell_trail':0.15, 'drop_param':2.5, 'level':3, 'pond':5, 'asset': 'DASH'},
          {'drop': 1, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.15, 'sell_trail':0.15, 'drop_param':2.5, 'level':3, 'pond':5, 'asset': 'MATIC'},
          {'drop': -1, 'profit': 0.5, 'k': 1.33, 'buy_trail':0.15, 'sell_trail':0.15, 'drop_param':2.5, 'level':3, 'pond':5, 'asset': 'MATIC'}]


backup = False

if __name__ == '__main__':
    
    if backup:
        
        sql_tables = init_database(sql_assets, True)
        account = Margin_account(Notifier())
        account.notifier.tables = sql_tables
        
        master = Symbol_combi()
        master.account = account
        
        with open("master.pickle", "rb") as f:
            master_back = pickle.load(f)
        
        master.symbol_list = master_back
        for i in master.symbol_list:
            i.master = master

        master.init_params(True)  
        print('Backup charged')
        
    else:
    
        sql_tables = init_database(sql_assets, False)
        account = Margin_account(Notifier())
        account.notifier.tables = sql_tables
        
        master = Symbol_combi()
        master.account = account
        master.add_symbols(inputs)
        master.init_params(False)    
        print('System initialized')
    
    print('Start Operating')
    
    while True:
        
        if master.engine_working == True:
            
            try:
                master.update_open_tr()
                backup_list = copy.deepcopy(master.symbol_list)
                
                for i in backup_list:
                    i.master = []
                with open("master.pickle", "wb") as f:
                    pickle.dump(backup_list, f)
                    
            except BinanceAPIException as e:
                print(f"Se produjo un error de la API de Binance: {e}")
                master.account.notifier.register_output('Error', 'general', 'general', 'Binance API error ' + str(e))
            except requests.exceptions.ReadTimeout as e:
                print(f"Error de tiempo de espera en la API de Binance: {e}")
                master.account.notifier.register_output('Error', 'general', 'general', 'Binance API error ' + str(e))
            except OperationalError as e:
                # Captura el error específico de SQLAlchemy
                print(f"Error de conexión a la base de datos: {e}")
            except Exception as e:
                print(f"ERROR NO IDENTIFICADO: {e}")
            time.sleep(5)
            
            try: # Conectarse con frontend y pedir instrucciones
                logic_front_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                logic_front_socket.settimeout(5) # Esperar 5 segundos antes de ejecutar la lógica
                logic_front_socket.connect(('localhost', 5556))
                
                # for i in master.symbol_list:
                #     i.master = []
                # backup = pickle.dumps(backup_list)
                # logic_front_socket.send(backup)
                texto = 'Hey frontend, carga el archivo master'
                mensaje = texto.encode('utf-8')
                logic_front_socket.send(mensaje)
                
                requests.post(url, data={'chat_id': '-1001802125737', 'text':  'Master charge order sent', 'parse_mode': 'HTML'})
                logic_front_socket.close()
                if logic_front_socket._closed:
                    requests.post(url, data={'chat_id': '-1001802125737', 'text':  'Frontend socket closed', 'parse_mode': 'HTML'})
                else:
                    requests.post(url, data={'chat_id': '-1001802125737', 'text':  'ERROR: Frontend socket not closed', 'parse_mode': 'HTML'})

                master.engine_working = False
                requests.post(url, data={'chat_id': '-1001802125737', 'text':  'Engine stopped', 'parse_mode': 'HTML'})

            except socket.error as e:
                #print(f"Error al establecer el tiempo de espera: {e}")
                pass
            except Exception as e:
                print('Error de socket: ', str(e))
                time.sleep(30) # Tiempo de espera entre iteraciones del bucle principal
            
        elif master.engine_working == False:
            
            try:
                # Crear servidor y esperar a que el frontend envíe instrucciones
                front_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                front_server.bind(('localhost', 5557))
                front_server.listen(1)
                conexion, direccion = front_server.accept()
                # backup_received = conexion.recv(4096)                
                
                # master.symbol_list = pickle.loads(backup_received)
                # for i in master.symbol_list:
                #     i.master = master
                data = conexion.recv(1024)
                texto = data.decode('utf-8')
                
                if texto == 'Hey logic, sigue con lo tuyo':
                
                    restart_symbols = delete(master.account.notifier.tables['symbols'])
                    sql_session.execute(restart_symbols)
                    
                    with open("master.pickle", "rb") as f:
                        master_back = pickle.load(f)
                    
                    master.symbol_list = master_back
                    for i in master.symbol_list:
                        i.master = master
                        i.trading_points()
                    
                    for symbol in master.symbol_list:
                        new_row = master.account.notifier.tables['symbols'](Name=symbol.name, Drop=symbol.drop, Profit=symbol.profit, K=symbol.k, Buy_trail=symbol.buy_trail, Sell_trail=symbol.sell_trail, Switch=symbol.switch, Symbol_status=symbol.status, Can_open=symbol.can_open, Can_average=symbol.can_average, Can_close=symbol.can_close, Can_open_trail=symbol.can_open_trail, Can_average_trail=symbol.can_average_trail, Can_close_trail=symbol.can_close_trail)
                        sql_session.add(new_row)
                    
                    sql_session.commit()
                
                    requests.post(url, data={'chat_id': '-1001802125737', 'text':  'Master received: ' + str(texto), 'parse_mode': 'HTML'})
                    conexion.close()
                    front_server.close()
                    if conexion._closed and front_server._closed:
                        requests.post(url, data={'chat_id': '-1001802125737', 'text':  'Logic socket closed', 'parse_mode': 'HTML'})
                    else:
                        requests.post(url, data={'chat_id': '-1001802125737', 'text':  'ERROR: Logic socket not closed', 'parse_mode': 'HTML'})
    
                    master.engine_working = True
                    requests.post(url, data={'chat_id': '-1001802125737', 'text':  'Engine started', 'parse_mode': 'HTML'})
                    
                elif texto == 'switch engine':
                    master.engine_working = True
                    requests.post(url, data={'chat_id': '-1001802125737', 'text':  'Engine started', 'parse_mode': 'HTML'})
                    
            except Exception as e:
                requests.post(url, data={'chat_id': '-1001802125737', 'text':  'ERROR: Master not received: ' + str(e), 'parse_mode': 'HTML'})
                master.engine_working = True
                requests.post(url, data={'chat_id': '-1001802125737', 'text':  'Engine restarted', 'parse_mode': 'HTML'})
