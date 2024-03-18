
import numpy as np
from datetime import datetime
import math
from binance.client import Client
from binance.exceptions import BinanceAPIException
from bot_database import sql_session
import traceback
from sqlalchemy import exc, delete

class Margin_account():
    
    def __init__(self, notifier) -> None:
        
        self.notifier = notifier
        self.base_coin = 'USDT'
        self.assets = []
        self.available_funds = 0
        self.max_leverage = 5
        self.max_leverage_funds = self.available_funds * self.max_leverage
        self.initial_amount = 100
        
        self.nav = 0
        self.margin = 999
        self.funds = 0
        self.long_acc = 0
        self.short_acc = 0
        
        self.balances = {}
        self.loans = {}
        self.t_balances = {self.base_coin:0}
        self.t_loans = {self.base_coin:0}
        self.teor_balances = {}
        
        self.have_open_order = {}
        #self.can_check_balance = []
        
        self.client = Client('KkepCPWDVxlgJBqns1Bl9vD0kxyop44uviwGZLUHHoK91lDENCvX0GxQeLfESzE7', 'wKWqIapmSnAvH5GJ1BwCdlg4s7Onq1FCu9iXszAtz3UWEEBmpovDBtU1IEd6RjYw')        
        self.price_precision = {'BTC': 2, 'ETH': 2, 'LTC': 2, 'ADA': 4, 'EOS': 3, 'XRP': 4, 'ETC': 2, 'TRX': 5, 
                                'VET': 5, 'LINK': 3, 'FET': 4, 'ATOM': 3, 'MATIC': 4, 'ALGO': 4, 'FTM': 4, 
                                'DOGE': 5, 'CHZ': 5, 'STX': 4, 'BCH': 1, 'COTI': 5, 'CHR': 4, 'MKR': 0, 
                                'DOT': 3, 'PAXG': 0, 'SOL': 2, 'TRB': 2, 'AVAX': 2, 'EGLD': 2, 'RUNE': 3, 
                                'UNI': 3, 'FIL': 3, 'INJ': 2, 'NEAR': 3, 'AXS': 3, 'ROSE': 5, 'GRT': 4, 
                                'CFX': 4, 'SUPER': 4, 'AR': 3, 'ICP': 3, 'SHIB': 8, 'MINA': 4, 'GALA': 5, 
                                'ENS': 2, 'RNDR': 3, 'IMX': 4, 'APE': 3, 'OP': 3, 'LUNC': 8, 'APT': 4, 
                                'AGIX': 5, 'ARB': 4, 'ID': 5, 'SUI': 4, 'MAV': 4}
        self.amount_precision = {'BTC': 5, 'ETH': 4, 'LTC': 3, 'ADA': 1, 'EOS': 1, 'XRP': 0, 'ETC': 2, 'TRX': 1, 
                                 'VET': 1, 'LINK': 2, 'FET': 0, 'ATOM': 2, 'MATIC': 1, 'ALGO': 0, 'FTM': 0, 
                                 'DOGE': 0, 'CHZ': 0, 'STX': 1, 'BCH': 3, 'COTI': 0, 'CHR': 0, 'MKR': 4, 
                                 'DOT': 2, 'PAXG': 4, 'SOL': 2, 'TRB': 2, 'AVAX': 2, 'EGLD': 2, 'RUNE': 1, 
                                 'UNI': 2, 'FIL': 2, 'INJ': 1, 'NEAR': 1, 'AXS': 2, 'ROSE': 1, 'GRT': 0, 
                                 'CFX': 0, 'SUPER': 0, 'AR': 2, 'ICP': 2, 'SHIB': 0, 'MINA': 1, 'GALA': 0, 
                                 'ENS': 2, 'RNDR': 2, 'IMX': 2, 'APE': 2, 'OP': 2, 'LUNC': 2, 'APT': 2,
                                 'AGIX': 0, 'ARB': 1, 'ID': 0, 'SUI': 1, 'MAV': 0}

        return
        
    def round_decimals_up(self, number, decimals):
        factor = 10 ** decimals
        return math.ceil(number * factor) / factor
    
    def round_decimals_down(self, number, decimals):
        factor = 10 ** decimals
        return math.floor(number * factor) / factor
    
    def get_base_balances(self):
        
        try:
            for item in self.client.get_margin_account()['userAssets']:
                if item['asset'] == self.base_coin:
                    self.balances[self.base_coin] = self.round_decimals_down(float(item['free']), 2)
                    self.loans[self.base_coin] = round(float(item['borrowed']) + float(item['interest']), 2)
        except Exception as e:
            print(f"Get base balance error: {e}")
            traceback.print_exc()
            self.notifier.register_output('Error', 'Base', 'general', 'Get base balance error: ' + str(e))
            self.notifier.send_error('Base', f"Get base balance error: {e}")
        return
    
    def get_asset_balances(self, asset):
        
        try:
            for item in self.client.get_margin_account()['userAssets']:
                if item['asset'] == asset:
                    self.balances[asset] = self.round_decimals_down(float(item['free']), self.amount_precision[asset])
                    self.loans[asset] = round(float(item['borrowed']) + float(item['interest']), self.amount_precision[asset])
        except Exception as e:
            print(f"Get asset balance error: {e}")
            traceback.print_exc()
            self.notifier.register_output('Error', asset, 'general', 'Get asset balance error: ' + str(e))
            self.notifier.send_error(asset, f"Get asset balance error: {e}")
        return
    
    def get_all_balances(self):
        self.get_base_balances()
        for asset in self.assets:
            self.get_asset_balances(asset)
        return
    
    def check_balances(self, symbol):
        
        try:
            real = self.balances[symbol.asset]
            teor = self.teor_balances[symbol.asset]
            loan = self.loans[symbol.asset]
            price = float(self.client.get_symbol_ticker(symbol=symbol.tic)['price'])
            
            if teor < 0:
                diff = round(abs(teor) - loan, self.amount_precision[symbol.asset])
            else:
                diff = round(teor - real, self.amount_precision[symbol.asset])
                
            diff_usdt = round(abs(diff)*price, 2)
            open_orders = self.client.get_open_margin_orders(symbol=symbol.tic)
            
            if len(open_orders) == 0 and self.have_open_order[symbol.asset]['Long'] == False and self.have_open_order[symbol.asset]['Short'] == False and diff_usdt > 9:
                
                if diff_usdt > 9:
                    if teor > 0:
                        if real - teor > 0:
                            action = 'SELL AND REPAY'
                            qty = round(real - teor, self.amount_precision[symbol.asset])
                            self.client.create_margin_order(symbol=symbol.tic, side='SELL', type='MARKET', quantity=qty, sideEffectType='AUTO_REPAY')
                        else:
                            action = 'MARGIN BUY'
                            qty = round(teor - real, self.amount_precision[symbol.asset])
                            self.client.create_margin_order(symbol=symbol.tic, side='BUY', type='MARKET', quantity=qty, sideEffectType='MARGIN_BUY')
                    else:
                        if abs(teor) - loan > 0:
                            action = 'MARGIN SELL'
                            qty = round(abs(teor) - loan, self.amount_precision[symbol.asset])
                            self.client.create_margin_order(symbol=symbol.tic, side='SELL', type='MARKET', quantity=qty, sideEffectType='MARGIN_BUY')
                        else:
                            action = 'BUY AND REPAY'
                            qty = round(loan - abs(teor), self.amount_precision[symbol.asset])
                            self.client.create_margin_order(symbol=symbol.tic, side='BUY', type='MARKET', quantity=qty, sideEffectType='AUTO_REPAY')
                            
                    self.notifier.send_balance_correction(symbol.asset, action, real, teor, loan, diff_usdt, diff, price)
                  
        except Exception as e:
            self.notifier.send_error('Check Balance', f"Error: {e}, Asset: {symbol.asset}, Name: {symbol.name}, Quantity: {qty}, Correction: {action}, Balance: {str(real)}, Balance_T: {str(teor)}, Loan: {loan}, Diff: {diff}")

        return [real, teor, loan, diff_usdt, diff, price]
            
    def calculate_nav(self, time):
        try:
            asset_value = self.balances[self.base_coin]
            liabilities = self.loans[self.base_coin]
            # self.nav = self.balances[self.base_coin] - self.loans[self.base_coin]
            for asset in self.assets:
                price = float(self.client.get_symbol_ticker(symbol=asset+self.base_coin)['price'])
                asset_value = asset_value + self.balances[asset]*price
                liabilities = liabilities + self.loans[asset]*price
                # self.nav = self.nav + self.balances[asset]*price - self.loans[asset]*price
                
            self.nav = asset_value - liabilities
            
            if liabilities == 0 or asset_value/liabilities > 999:
                self.margin = 999
            else:
                self.margin = asset_value/liabilities
            
            margin_account = self.client.get_margin_account()
            if float(margin_account['totalLiabilityOfBtc']) == 0:
                margin = 999
            else:
                margin = margin_account['marginLevel']
            btc_price = float(self.client.get_symbol_ticker(symbol='BTCUSDT')['price'])
            
            new_row = self.notifier.tables['nav'](Date=str(time), Nav=self.nav, Bnb_nav=float(margin_account['totalNetAssetOfBtc'])*btc_price, Margin=self.margin, Bnb_margin=margin, Acc=round(self.short_acc-self.long_acc))
            sql_session.add(new_row)
            
            try:
                sql_session.commit()
            except exc.OperationalError as e:
                self.notifier.send_error('NAV Commit', f"Error de conexión a la base de datos: {e}")
                sql_session.rollback()
            self.notifier.register_output('Info', 'general', 'general', 'Nav calculated')
            
        except Exception as e:
            self.notifier.register_output('Error', 'general', 'general', 'Nav calculating error: ' + str(e))
            self.notifier.send_error('NAV', f"Nav calculating error: {e}")
        return       
    
    def check_funds(self, buy_amount, side, price):
        
        if side == 'BUY':
            if self.funds - buy_amount < -self.max_leverage_funds or self.long_acc + buy_amount > self.max_leverage_funds:
                free_funds = self.max_leverage_funds - self.long_acc
                if free_funds > 15:
                    output_amount = free_funds
                else:
                    output_amount = 0
            else:
                output_amount = buy_amount
        else:
            if self.funds + buy_amount > self.max_leverage_funds or self.short_acc + buy_amount > self.max_leverage_funds:
                free_funds = self.max_leverage_funds - self.short_acc
                if free_funds > 15:
                    output_amount = free_funds
                else:
                    output_amount = 0
            else:
                output_amount = buy_amount
            
        return output_amount/price
    
    def create_buy_order(self, symbol, buy_amount_0, price, action, actual_price):

        buy_amount = self.check_funds(buy_amount_0*price, 'BUY', price)
        check = False
        
        if buy_amount > 0:
            order_qty = self.round_decimals_up(max(buy_amount, self.initial_amount/price), self.amount_precision[symbol.asset])
            order_price = round(price, self.price_precision[symbol.asset])
            stop_price = round((actual_price*1.0005), self.price_precision[symbol.asset])
            
            try:
                self.get_asset_balances(symbol.asset)
    
                for i in self.client.get_margin_account()['userAssets']:
                    if i['asset'] == 'USDT':
                        free_base = float(i['free'])
    
                if free_base > order_qty*price and self.loans[symbol.asset] > 0:
                    side_effect = 'AUTO_REPAY'
                else:
                    side_effect = 'MARGIN_BUY'
                
                try:
                    buy_open_order = self.client.create_margin_order(symbol=symbol.tic, side='BUY', type='STOP_LOSS_LIMIT', quantity=order_qty, price=order_price, stopPrice=stop_price, sideEffectType=side_effect, timeInForce='GTC')
                    buy_open_order['action'] = action
                    symbol.open_order_id = buy_open_order
                    if symbol.side == 'Long':
                        self.have_open_order[symbol.asset]['Long'] = True
                    else:
                        self.have_open_order[symbol.asset]['Short'] = True
                    check = True
                # except BinanceAPIException as e:
                #     if e.code == -2010:
                #         buy_open_order = self.client.create_margin_order(symbol=symbol.tic, side='BUY', type='LIMIT', quantity=order_qty, price=order_price, sideEffectType=side_effect, timeInForce='GTC')
                #         # self.notifier.send_order_placed_trial(action, symbol, price, buy_amount, 'second')
                #         buy_open_order['action'] = action
                #         symbol.open_order_id = buy_open_order
                #         if symbol.side == 'Long':
                #             self.have_open_order[symbol.asset]['Long'] = True
                #         else:
                #             self.have_open_order[symbol.asset]['Short'] = True
                #         check = True
                except Exception as e:
                    self.notifier.send_error(symbol.tic, f"Buy Order Creation Failed: {e};  Action: {action};  Qty: {order_qty}; Free Base: {free_base}; Price: {order_price}; Stop Price: {stop_price}; Effect: {side_effect}; Tipo: {type(e)}; Args: {e.args}; Linea: {e.__traceback__.tb_lineno}")

                
            except BinanceAPIException as e:
                if e.code == -3045:
                    self.notifier.register_output('Warn', symbol.asset, symbol.side, f"Buy Order Creation Failed: {e};  Action: {action};  Amount: {buy_amount}; Price: {price}; Effect: {side_effect}")
                elif e.code == -3044:
                    self.notifier.register_output('Warn', symbol.asset, symbol.side, f"Buy Order Creation Failed: {e};  Action: {action};  Amount: {buy_amount}; Price: {price}; Effect: {side_effect}")
                elif e.code == -3007:
                    self.notifier.register_output('Warn', symbol.asset, symbol.side, f"Buy Order Creation Failed: {e};  Action: {action};  Amount: {buy_amount}; Price: {price}; Effect: {side_effect}")
                else:
                    self.notifier.register_output('Error', symbol.asset, symbol.side, f"Buy Order Creation Failed: {e};  Action: {action};  Amount: {buy_amount}; Price: {price}; Effect: {side_effect}")
                    self.notifier.send_error(symbol.name, f"Buy Order Creation Failed: {e};  Action: {action};  Amount: {buy_amount}; Price: {price}; Effect: {side_effect}")

            except Exception as e:
                self.notifier.send_error(symbol.name, f"Buy Order Creation Failed: {e};  Action: {action};  Qty: {order_qty}; Free Base: {free_base}; Price: {order_price}; Stop Price: {stop_price}; Effect: {side_effect}; Tipo: {type(e)}; Args: {e.args}; Linea: {e.__traceback__.tb_lineno}")

        return check
    
    def create_sell_order(self, symbol, buy_amount_0, price, action, actual_price):
        
        buy_amount = self.check_funds(buy_amount_0*price, 'SELL', price)
        check = False
        
        if buy_amount > 0:
            order_qty = max(self.round_decimals_down(buy_amount, self.amount_precision[symbol.asset]), self.round_decimals_up(self.initial_amount/price, self.amount_precision[symbol.asset]))
            order_price = round(price, self.price_precision[symbol.asset])
            stop_price = round(actual_price*0.9995, self.price_precision[symbol.asset])

            try:
                self.get_base_balances()
                
                for i in self.client.get_margin_account()['userAssets']:
                    if i['asset'] == symbol.asset:
                        free_asset = float(i['free'])
                        
                if free_asset > order_qty and self.loans[self.base_coin] > 0:
                    side_effect = 'AUTO_REPAY'
                else:
                    side_effect = 'MARGIN_BUY'
            
                try:
                    sell_open_order = self.client.create_margin_order(symbol=symbol.tic, side='SELL', type='STOP_LOSS_LIMIT', quantity=order_qty, price=order_price, stopPrice=stop_price, sideEffectType=side_effect, timeInForce='GTC')
                    sell_open_order['action'] = action
                    symbol.open_order_id = sell_open_order
                    if symbol.side == 'Long':
                        self.have_open_order[symbol.asset]['Long'] = True
                    else:
                        self.have_open_order[symbol.asset]['Short'] = True
                    check = True
                # except BinanceAPIException as e:
                #     if e.code == -2010:
                #         sell_open_order = self.client.create_margin_order(symbol=symbol.tic, side='SELL', type='LIMIT', quantity=order_qty, price=order_price, sideEffectType=side_effect, timeInForce='GTC')
                #         # self.notifier.send_order_placed_trial(action, symbol, price, buy_amount, 'second')
                #         sell_open_order['action'] = action
                #         symbol.open_order_id = sell_open_order
                #         if symbol.side == 'Long':
                #             self.have_open_order[symbol.asset]['Long'] = True
                #         else:
                #             self.have_open_order[symbol.asset]['Short'] = True
                #         check = True
                except Exception as e:
                    self.notifier.send_error(symbol.tic, f"Sell Order Creation Failed: {e};  Action: {action};  Qty: {order_qty}; Free Asset: {free_asset}; Price: {order_price}; Stop Price: {stop_price}; Effect: {side_effect}; Tipo: {type(e)}; Args: {e.args}; Linea: {e.__traceback__.tb_lineno}")

                
            except BinanceAPIException as e:
                if e.code == -3045:
                    self.notifier.register_output('Warn', symbol.asset, symbol.side, f"Sell Order Creation Failed: {e};  Action: {action};  Amount: {order_qty}; Price: {order_price}; Effect: {side_effect}")
                elif e.code == -3044:
                    self.notifier.register_output('Warn', symbol.asset, symbol.side, f"Sell Order Creation Failed: {e};  Action: {action};  Amount: {order_qty}; Price: {order_price}; Effect: {side_effect}")
                elif e.code == -3007:
                    self.notifier.register_output('Warn', symbol.asset, symbol.side, f"Buy Order Creation Failed: {e};  Action: {action};  Amount: {order_qty}; Price: {order_price}; Effect: {side_effect}")
                else:
                    self.notifier.register_output('Error', symbol.asset, symbol.side, f"Sell Order Creation Failed: {e};  Action: {action};  Amount: {order_qty}; Price: {order_price}; Effect: {side_effect}")
                    self.notifier.send_error(symbol.name, f"Sell Order Creation Failed: {e};  Action: {action};  Amount: {order_qty}; Price: {order_price}; Effect: {side_effect}")

            except Exception as e:
                self.notifier.send_error(symbol.name, f"Sell Order Creation Failed: {e};  Action: {action};  Qty: {order_qty}; Free Asset: {free_asset}; Price: {order_price}; Stop Price: {stop_price}; Effect: {side_effect}; Tipo: {type(e)}; Args: {e.args}; Linea: {e.__traceback__.tb_lineno}")

        return check
    
    def check_partial_order(self, symbol):
        
        try:
            order = symbol.open_order_id        
            open_order = self.client.get_margin_order(symbol=order['symbol'], orderId=order['orderId'])
            
            executed_amount, executed_price= np.array([]), np.array([])
            for trade in self.client.get_margin_trades(symbol=order['symbol']):
                if trade['orderId'] == order['orderId']:
                    executed_amount = np.append(executed_amount, [float(trade['qty'])])
                    executed_price = np.append(executed_price, [float(trade['price'])])
                    if trade['commissionAsset'] == self.base_coin:
                        comision = float(trade['commission'])
                        symbol.commission = symbol.commission + comision
                    else:
                        try:
                            asset_price = float(self.client.get_symbol_ticker(symbol=trade['commissionAsset']+self.base_coin)['price'])
                            comision = float(trade['commission']) * asset_price
                            symbol.commission = symbol.commission + comision
                        except Exception as e:
                            self.notifier.send_error(symbol.name, 'Check orded, price reading error: ' + str(e))
    
            total_amount = sum(executed_amount)
            average_price = np.dot(executed_price, executed_amount)/total_amount
            
            self.notifier.register_output('Action', symbol.asset, symbol.side, order['action'] + ' Order Partially Filled ' + str(open_order['orderId']))
                
        except Exception as e:
            self.notifier.send_error('Check Partial Order', f"Error: {e}, Name: {symbol.name}, ID: {symbol.open_order_id['orderId']}")

        return total_amount, average_price
    
    def check_filled_order(self, symbol):
        
        try:
            order = symbol.open_order_id        
            open_order = self.client.get_margin_order(symbol=order['symbol'], orderId=order['orderId'])
            
            executed_amount, executed_price, executed_commission = np.array([]), np.array([]), np.array([])
            for trade in self.client.get_margin_trades(symbol=order['symbol']):
                if trade['orderId'] == order['orderId']:
                    executed_amount = np.append(executed_amount, [float(trade['qty'])])
                    executed_price = np.append(executed_price, [float(trade['price'])])
                    date0 = str(trade['time'])[:-3]
                    date = datetime.fromtimestamp(int(date0))
                    if trade['commissionAsset'] == self.base_coin:
                        comision = float(trade['commission'])
                        executed_commission = np.append(executed_commission, [comision])
                        symbol.commission = symbol.commission + comision
                    else:
                        try:
                            asset_price = float(self.client.get_symbol_ticker(symbol=trade['commissionAsset']+self.base_coin)['price'])
                            comision = float(trade['commission']) * asset_price
                            executed_commission = np.append(executed_commission, [comision])
                            symbol.commission = symbol.commission + comision
                        except Exception as e:
                            self.notifier.send_error(symbol.name, 'Check orded, price reading error: ' + str(e))
    
            total_amount = sum(executed_amount)
            average_price = np.dot(executed_price, executed_amount)/total_amount
            total_commission = np.sum(executed_commission)
            self.notifier.register_output('Action', symbol.asset, symbol.side, order['action'] + ' Order Filled ' + str(open_order['orderId']))
            
            symbol.open_order_id = []
            if symbol.side == 'Long':
                self.have_open_order[symbol.asset]['Long'] = False
            else:
                self.have_open_order[symbol.asset]['Short'] = False
    
            if order['action'] == 'OPEN':
                symbol.open_order(date, average_price, total_amount, total_commission)
            elif order['action'] == 'AVERAGE':
                symbol.average_order(date, average_price, total_amount, total_commission)
            elif order['action'] == 'CLOSE':
                symbol.close_order(date, average_price, total_amount, total_commission)
                
            #self.can_check_balance = symbol
           
        except Exception as e:
            self.notifier.send_error('Check Filled Order', f"Error: {e}, Name: {symbol.name}, ID: {symbol.open_order_id['orderId']}")
            
        return
    
__all__ = ['Margin_account']
