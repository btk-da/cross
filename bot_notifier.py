
from datetime import datetime
import requests
import numpy as np
from bot_database import sql_session
from sqlalchemy import exc


class Notifier():
    
    def __init__(self) -> None:
        
        self.tables = {}
        self.token = '6332743294:AAFKcqzyfKzXAPSGhR6eTKLPMyx0tpCzeA4'
        
        self.eqs = {'gorka':10908, 'aita':41998, 'saioa':24000, 'inaki':15789, 'nacho':1361, 'total':98684}
        self.parts = {'gorka':73.32, 'aita':21.77, 'saioa':7.3, 'inaki':4.8, 'nacho':0.41}
        self.ids = {'gorka':'-1002116297039', 'aita':'-1001517241898', 'saioa':'-1002118100147', 'inaki':'-1002079190459', 'nacho':'-1002080234130', 'error':'-1002041194998', 'comms':'-1001966519898', 'general':'-1002023987289'}
        
    def send_order_placed_trial(self, action, symbol, price, amount, place):
        
        message = ('#' + str(action) + '_TRY_TO_PLACE' + '\n' + 
                   'Place: ' + str(place) + '\n' +
                   'Symbol: ' + str(symbol.name) + '\n' + 
                   'Price: ' + str(price) + '\n' + 
                   'Amount: ' + str(round(amount, 5)) + '\n' + 
                   'Cost: ' + str(round(amount*price, 2)) + '$')
        try:  
            requests.post('https://api.telegram.org/bot' + self.token + '/sendMessage', data={'chat_id': self.ids['comms'], 'text': message, 'parse_mode': 'HTML'})
            self.register_output('Action', symbol.asset, symbol.side, str(action) + ' placed')
        except Exception as e:
            print(str(action) + ' Placed Order Post Error')
            self.register_output('Error', symbol.asset, symbol.side, 'Order Placed Post Error: ' + str(e))
        return
    def send_order_placed(self, action, symbol, price, amount):
        
        message = ('#' + str(action) + '_PLACED' + '\n' + 
                   'Symbol: ' + str(symbol.name) + '\n' + 
                   'Price: ' + str(price) + '\n' + 
                   'Amount: ' + str(round(amount, 5)) + '\n' + 
                   'Cost: ' + str(round(amount*price, 2)) + '$')
        try:  
            requests.post('https://api.telegram.org/bot' + self.token + '/sendMessage', data={'chat_id': self.ids['comms'], 'text': message, 'parse_mode': 'HTML'})
            self.register_output('Action', symbol.asset, symbol.side, str(action) + ' placed')
        except Exception as e:
            print(str(action) + ' Placed Order Post Error')
            self.register_output('Error', symbol.asset, symbol.side, 'Order Placed Post Error: ' + str(e))
        return
    
    def send_open_order_filled(self, price, amount, symbol):
        
        message = ('#OPEN_FILLED' + '\n' + 
                   'Symbol: ' + str(symbol.name) + '\n' + 
                   'Price: ' + str(price) + '\n' + 
                   'Amount: ' + str(round(amount, symbol.master.account.amount_precision[symbol.asset])) + '\n' + 
                   'Cost: ' + str(round(symbol.acc, 2)) + '$' + '\n' +
                   'Average Point: ' + str(round(symbol.average_point, symbol.master.account.price_precision[symbol.asset])) + '\n' +
                   'Close Point: ' + str(round(symbol.close_point, symbol.master.account.price_precision[symbol.asset])))
        try:  
            requests.post('https://api.telegram.org/bot' + self.token + '/sendMessage', data={'chat_id': self.ids['comms'], 'text': message, 'parse_mode': 'HTML'})
            self.register_output('Action', symbol.asset, symbol.side, 'Open filled')
        except Exception as e:
            print('Open Order Post Error')
            self.register_output('Error', symbol.asset, symbol.side, 'Open Order Filled Post Error: ' + str(e))
        
        return
    
    def send_average_order_filled(self, price, amount, symbol, last_drop):
        
        message = ('#AVERAGING_FILLED' + '\n' + 
                   'Symbol: ' + str(symbol.name) + '\n' + 
                   'Buy Level: ' + str(symbol.buy_level) + '\n' +
                   'Drop: ' + str(abs(round(((price/symbol.open_price - 1) * 100), 2))) + '%' + '\n' +
                   'Last Drop: ' + str(round(last_drop, 2)) + '\n' +
                   'Price: ' + str(round(price, symbol.master.account.price_precision[symbol.asset])) + '\n' +
                   'Amount: ' + str(amount) + ' (' + str(round(amount*price, 2)) + '$) \n' + 
                   'Cost: ' + str(round(symbol.acc,2)) + '$' + '\n' +
                   'Average Price: ' + str(round(symbol.average_price, symbol.master.account.price_precision[symbol.asset])) + '\n' +
                   'Average Point: ' + str(round(symbol.average_point, symbol.master.account.price_precision[symbol.asset])) + '\n' +
                   'Close Point: ' + str(round(symbol.close_point, symbol.master.account.price_precision[symbol.asset])))
        try:  
            requests.post('https://api.telegram.org/bot' + self.token + '/sendMessage', data={'chat_id': self.ids['comms'], 'text': message, 'parse_mode': 'HTML'})
            self.register_output('Action', symbol.asset, symbol.side, 'Average filled')
        except Exception as e:
            print('Average Order Post Error')
            self.register_output('Error', symbol.asset, symbol.side, 'Average Order Filled Post Error: ' + str(e))
        
        return
    
    def send_transaction_closed_filled(self, symbol, profit, usd_profit, commission, price, covered):
        
        self.eqs['total'] = self.eqs['total'] + usd_profit
        
        message = ('#OPERACION CERRADA' + '\n' + 
                   'Symbol: ' + str(symbol.name) + '\n' + 
                   'Coste: ' + str(round(symbol.acc,2)) + '$' + '\n' +
                   'Beneficio (%): ' + str(round(profit*100, 2)) + '% \n' + 
                   'Beneficio ($): ' + str(round(float(usd_profit), 3)) + '\n' +
                   '% Cubierto: ' + str(covered) + '\n' +
                   'Precio: ' + str(round(price, symbol.master.account.price_precision[symbol.asset])) + '\n' +
                   'Duracion: ' + str(symbol.duration) + '\n' + 
                   'Comision ($): ' + str(np.around(commission, 5)) + '\n' +
                   'Beneficio Total: ' + str(round(self.eqs['total'], 2)))
        
        self.operation_client(usd_profit)        
        try:
            requests.post('https://api.telegram.org/bot' + self.token + '/sendMessage', data={'chat_id': self.ids['general'], 'text': message, 'parse_mode': 'HTML'})
            self.register_output('Action', symbol.asset, symbol.side, 'Close filled')
        except Exception as e:
            self.register_output('Error', symbol.asset, symbol.side, 'Transaction Closed Post Error: ' + str(e))
        
        return
    
    def operation_client(self, usd_profit):
        
        for client in self.parts:
            client_profit = float(usd_profit)*self.parts[client]/100
            self.eqs[client] = self.eqs[client] + client_profit
        
            message = ('#OPERATION CLOSED' + '\n' + 
                       'Profit ($): ' + str(round(client_profit, 4)) + '\n' +
                       'Total: ' + str(round(self.eqs[client], 2)))
            try:
                requests.post('https://api.telegram.org/bot' + self.token + '/sendMessage', data={'chat_id': self.ids[client], 'text': message, 'parse_mode': 'HTML'})
            except Exception as e:
                print('Transaction Closed Post Error' + str(e))
        
        return
    
    def register_output(self, type_, asset, side, content):
        
        time = datetime(datetime.now().year, datetime.now().month, datetime.now().day, datetime.now().hour, datetime.now().minute, datetime.now().second)
        new_row = self.tables['output'](Date=str(time), Type=type_, Asset=asset, Side=side, Content=content)
        sql_session.add(new_row)
        try:
            sql_session.commit()
        except exc.OperationalError as e:
            print(f"Error de conexión a la base de datos: {e}")
            sql_session.rollback()  # Revertir cambios pendientes, si los hay
        return
    
    def send_error(self, symbol, error):
        
        message = ('#ERROR' + '\n' + 
                   'Symbol: ' + str(symbol) + '\n' + 
                   'Error: ' + error)
        try:  
            requests.post('https://api.telegram.org/bot' + self.token + '/sendMessage', data={'chat_id': self.ids['error'], 'text': message, 'parse_mode': 'HTML'})
        except Exception as e:
            print('Send Error Post Error' + str(e))
        return
    
    def send_order_check_fail(self, symbol, order):
        
        message = ('#ORDER PLACING FAILED' + '\n' + 
                   'Symbol: ' + str(symbol.name) + '\n' +
                   'Order: ' + str(order) + '\n' +
                   'Can Open: ' + symbol.can_open + '\n' +
                   'Can Open Trail : ' + symbol.can_open_trail + '\n' +
                   'Can Average: ' + symbol.can_average + '\n' +
                   'Can Average Trail: ' + symbol.can_average_trail + '\n' +
                   'Can Close: ' + symbol.can_close + '\n' +
                   'Can Close Trail: ' + symbol.can_close_trail)
        try:  
            requests.post('https://api.telegram.org/bot' + self.token + '/sendMessage', data={'chat_id': self.ids['error'], 'text': message, 'parse_mode': 'HTML'})
        except Exception as e:
            print('Send Error Post Error' + str(e))
        return
    
    def send_balance_correction(self, asset, action, balance, t_balance, loan, diff_usdt, diff, price):
                
        message = ('#BALANCE CORRECTION' + '\n' + 
                   'Asset: ' + str(asset) + '\n' + 
                   'Action: ' + str(action) + '\n' + 
                   'Balance: ' + str(round(balance, 5)) + '\n' + 
                   'T_Balance: ' + str(round(t_balance, 5)) + '\n' + 
                   'Loan: ' + str(round(loan, 5)) + '\n' + 
                   'Diff USDT: ' + str(round(diff_usdt)) + '\n' + 
                   'Diff: ' + str(round(diff, 5)))
        try:  
            requests.post('https://api.telegram.org/bot' + self.token + '/sendMessage', data={'chat_id': self.ids['comms'], 'text': message, 'parse_mode': 'HTML'})
        except Exception as e:
            print('Balances Post Error' + str(e))
        
        return
    
__all__ = ['Notifier']