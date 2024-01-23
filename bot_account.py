
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
        self.max_leverage = 4
        self.max_leverage_funds = self.available_funds * self.max_leverage
        # self.indiv_max_leverage_funds = self.max_leverage_funds/29
        self.initial_amount = 10
        
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
        self.can_check_balance = []
        
        self.client = Client('HxC4DjBJjOv6lqiDdgnF1c7SW3SYYKnmvRyg1KAW4UY4oa5Ndbz3yAi7Z4TtXky9', 'RwwVEqxVzRmtcxf8sAvMcu6kwz6OxEtxsbcTBDTjgHrsmzqgpCjFcBq0aeW93rEU')
        self.price_precision = {'BTC':2, 'ETH':2, 'BNB':1, 'XRP':4, 'ADA':4, 'LTC':2, 'SOL':2, 'ATOM':3, 'BCH':1, 
                                'DOGE':5, 'DOT':3, 'EOS':3, 'LINK':3, 'TRX':5, 'SHIB':8, 'AVAX':2, 'XLM':4, 'UNI':3, 
                                'ETC':2, 'FIL':3, 'HBAR':4, 'VET':5, 'NEAR':3, 'GRT':4, 'AAVE':2, 'DASH':2, 'MATIC':4, 
                                'ICP':3 , 'RUNE':3, 'IMX':4, 'OP':3, 'LDO':3, 'INJ':2, 'USDT':2}
        self.amount_precision = {'BTC':5, 'ETH':4, 'BNB':3, 'XRP':0, 'ADA':1, 'LTC':3, 'SOL':2, 'ATOM':2, 'BCH':3,
                                'DOGE':0, 'DOT':2, 'EOS':1, 'LINK':2, 'TRX':1, 'SHIB':0, 'AVAX':2, 'XLM':0, 'UNI':2, 
                                'ETC':2, 'FIL':2, 'HBAR':0, 'VET':1, 'NEAR':1, 'GRT':0, 'AAVE':3, 'DASH':3, 'MATIC':1, 
                                'ICP':2 , 'RUNE':1, 'IMX':2, 'OP':2, 'LDO':2, 'INJ':1, 'USDT':2}
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
        
        open_orders = self.client.get_open_margin_orders(symbol=symbol.tic)
        
        if len(open_orders) == 0 and self.have_open_order[symbol.asset]['Long'] == False and self.have_open_order[symbol.asset]['Short'] == False:
            
            real = self.balances[symbol.asset]
            teor = self.teor_balances[symbol.asset]
            loan = self.loans[symbol.asset]
            
            price = float(self.client.get_symbol_ticker(symbol=symbol.tic)['price'])
            
            diff = round(teor - real, self.amount_precision[symbol.asset])
            diff_usd = round(abs(diff)*price, 2)
            
            if diff_usd > 9:
                self.notifier.send_error('Check balance', f"Correccion de balances: Symbol: {symbol.name}, Diff: {diff}, Diff Usd: {diff_usd}")
                
            # try:
            #     price = float(self.client.get_symbol_ticker(symbol=symbol.tic)['price'])
            #     self.get_asset_balances(symbol.asset)
        
            #     real = self.balances[symbol.asset]
            #     teor = round(self.t_balances[symbol.asset], self.amount_precision[symbol.asset])
            #     loan = self.loans[symbol.asset]
            #     correction = False
                
            #     if teor >= 0:
            #         diff_usd = round((teor - loan), self.amount_precision[symbol.asset])
                    
            #         if abs(diff_usd) * price > 6:
                        
            #             if diff_usd > 0:
            #                 correction = 'BUY ' + str(abs(diff_usd))
            #                 self.client.create_margin_order(symbol=symbol.tic, side='BUY', type='MARKET', quantity=round(diff_usd, self.amount_precision[symbol.asset]), sideEffectType='AUTO_REPAY')
            #             elif diff_usd < 0:
            #                 correction = 'SELL ' + str(abs(diff_usd))
            #                 self.client.create_margin_order(symbol=symbol.tic, side='SELL', type='MARKET', quantity=abs(round(diff_usd, self.amount_precision[symbol.asset])), sideEffectType='AUTO_REPAY')
                            
            #                 self.get_asset_balances(symbol.asset)
            #                 if self.loans[symbol.asset] > 0:
            #                     self.client.repay_margin_loan(asset=symbol.asset, amount=self.loans[symbol.asset])
                
            #     else:
            #         diff_usd = round((abs(teor) - loan), self.amount_precision[symbol.asset])
                    
            #         if abs(diff_usd) * price > 6:
                        
            #             if diff_usd > 0:
            #                 correction = 'BORROW ' + str(abs(round(diff_usd, self.amount_precision[symbol.asset])))                    
            #                 self.client.create_margin_loan(asset=symbol.asset, amount=diff_usd)
            #             elif diff_usd < 0:
            #                 correction = 'REPAY ' + str(abs(round(diff_usd, self.amount_precision[symbol.asset])))  
            #                 self.client.repay_margin_loan(asset=symbol.asset, amount=abs(diff_usd))
                            
            #             self.get_asset_balances(symbol.asset)
            #             if self.balances[symbol.asset] > 0:
            #                 self.client.create_margin_order(symbol=symbol.tic, side='SELL', type='MARKET', quantity=abs(round(self.balances[symbol.asset], self.amount_precision[symbol.asset])), sideEffectType='AUTO_REPAY')
                            
            #         if loan > 0 and real >= loan:
            #             correction = 'REPAY ' + str(abs(loan)) 
            #             self.client.repay_margin_loan(asset=symbol.asset, amount=loan)
                
            #     if correction != False:
            #         self.notifier.send_error('Check balance', f"Correccion de balances: Symbol: {symbol.name}, Correccion: {correction}")

                    
            #     # new_row = self.notifier.tables['balances'](Date=str(time), Asset = symbol.asset, Base_balance = self.balances[self.base_coin], Base_t_balance = self.t_balances[self.base_coin], Base_loan = self.loans[self.base_coin], Asset_balance = self.balances[symbol.asset], Asset_t_balance = round(self.t_balances[symbol.asset], self.amount_precision[symbol.asset]), Asset_loan = self.loans[symbol.asset], Correction = correction, Action = action)
            #     # sql_session.add(new_row)
            #     # try:
            #     #     sql_session.commit()
            #     # except exc.OperationalError as e:
            #     #     self.notifier.send_error('Check balance Commit', f"Error de conexión a la base de datos: {e}, Symbol: {symbol.name}")
            #     #     sql_session.rollback()
                
            # except BinanceAPIException as e:
            #     if e.code == -1100:
            #         self.notifier.send_error('Check Balance', f"Error: {e}, Asset: {symbol.asset}, Name: {symbol.name}, Correction: {correction}, Balance: {str(real)}, Balance_T: {str(teor)}, Loan: {loan}")
            #     elif e.code == -3041:
            #         self.notifier.send_error('Check Balance', f"Error: {e}, Asset: {symbol.asset}, Name: {symbol.name}, Correction: {correction}, Balance: {str(real)}, Balance_T: {str(teor)}, Loan: {loan}")
                
            # except Exception as e:
            #     self.notifier.send_error('Check Balance', f"Error: {e}, Asset: {symbol.asset}, Name: {symbol.name}, Correction: {correction}, Balance: {str(real)}, Balance_T: {str(teor)}, Loan: {loan}")

        return
            
    def calculate_nav(self, time):
        try:
            asset_value = self.balances[self.base_coin]
            liabilities = self.loans[self.base_coin]
            self.nav = self.balances[self.base_coin] - self.loans[self.base_coin]
            for asset in self.assets:
                price = float(self.client.get_symbol_ticker(symbol=asset+self.base_coin)['price'])
                asset_value = asset_value + self.balances[asset]*price
                liabilities = liabilities + self.loans[asset]*price
                self.nav = self.nav + self.balances[asset]*price - self.loans[asset]*price
            
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
            
            new_row = self.notifier.tables['nav'](Date=str(time), Nav=self.nav, Bnb_nav=float(margin_account['totalNetAssetOfBtc'])*btc_price)
            sql_session.add(new_row)
            new_row = self.notifier.tables['margin'](Date=str(time), Margin=margin)
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
        # self.notifier.send_order_placed_trial(action, symbol, price, buy_amount)
        
        if buy_amount > 0:
            order_qty = self.round_decimals_up(max(buy_amount, self.initial_amount/price), self.amount_precision[symbol.asset])
            order_price = round(price, self.price_precision[symbol.asset])
            stop_price = round((actual_price*1.001), self.price_precision[symbol.asset])
            
            try:
                self.notifier.send_order_placed_trial(action, symbol, price, buy_amount, 'zero')

                self.get_asset_balances(symbol.asset)
    
                if self.loans[symbol.asset] > 0:
                    side_effect = 'AUTO_REPAY'
                else:
                    side_effect = 'MARGIN_BUY'
                    
                try:
                    self.notifier.send_order_placed_trial(action, symbol, price, buy_amount, 'first pre')
                    buy_open_order = self.client.create_margin_order(symbol=symbol.tic, side='BUY', type='STOP_LOSS_LIMIT', quantity=order_qty, price=order_price, stopPrice=stop_price, sideEffectType=side_effect, timeInForce='GTC')
                    self.notifier.send_order_placed_trial(action, symbol, price, buy_amount, 'first')
                    buy_open_order['action'] = action
                    symbol.open_order_id = buy_open_order
                    if symbol.side == 'Long':
                        self.have_open_order[symbol.asset]['Long'] = True
                    else:
                        self.have_open_order[symbol.asset]['Short'] = True
                    check = True
                except BinanceAPIException as e:
                    if e.code == -2010:
                        buy_open_order = self.client.create_margin_order(symbol=symbol.tic, side='BUY', type='LIMIT', quantity=order_qty, price=order_price, sideEffectType=side_effect, timeInForce='GTC')
                        self.notifier.send_order_placed_trial(action, symbol, price, buy_amount, 'second')
                        buy_open_order['action'] = action
                        symbol.open_order_id = buy_open_order
                        if symbol.side == 'Long':
                            self.have_open_order[symbol.asset]['Long'] = True
                        else:
                            self.have_open_order[symbol.asset]['Short'] = True
                        check = True
                
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
                self.notifier.send_error(symbol.name, f"Buy Order Creation Failed: {e};  Action: {action};  Amount: {buy_amount}; Price: {price}; Effect: {side_effect}; Tipo: {type(e)}; Args: {e.args}; Linea: {e.__traceback__.tb_lineno}")

        return check
    
    def create_sell_order(self, symbol, buy_amount_0, price, action, actual_price):
        
        buy_amount = self.check_funds(buy_amount_0*price, 'SELL', price)
        check = False
        # self.notifier.send_order_placed_trial(action, symbol, price, buy_amount)
        
        if buy_amount > 0:
            order_qty = self.round_decimals_down(max(buy_amount, self.initial_amount/price), self.amount_precision[symbol.asset])
            order_price = round(price, self.price_precision[symbol.asset])
            stop_price = round(actual_price*0.999, self.price_precision[symbol.asset])
            
            try:
                self.get_base_balances()
                
                if self.loans[self.base_coin] > 0:
                    side_effect = 'AUTO_REPAY'
                else:
                    side_effect = 'MARGIN_BUY'
                
                try:
                    sell_open_order = self.client.create_margin_order(symbol=symbol.tic, side='SELL', type='STOP_LOSS_LIMIT', quantity=order_qty, price=order_price, stopPrice=stop_price, sideEffectType=side_effect, timeInForce='GTC')
                    self.notifier.send_order_placed_trial(action, symbol, price, buy_amount, 'first')
                    sell_open_order['action'] = action
                    symbol.open_order_id = sell_open_order
                    if symbol.side == 'Long':
                        self.have_open_order[symbol.asset]['Long'] = True
                    else:
                        self.have_open_order[symbol.asset]['Short'] = True
                    check = True
                except BinanceAPIException as e:
                    if e.code == -2010:
                        sell_open_order = self.client.create_margin_order(symbol=symbol.tic, side='SELL', type='LIMIT', quantity=order_qty, price=order_price, sideEffectType=side_effect, timeInForce='GTC')
                        self.notifier.send_order_placed_trial(action, symbol, price, buy_amount, 'second')
                        sell_open_order['action'] = action
                        symbol.open_order_id = sell_open_order
                        if symbol.side == 'Long':
                            self.have_open_order[symbol.asset]['Long'] = True
                        else:
                            self.have_open_order[symbol.asset]['Short'] = True
                        check = True
                
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
                self.notifier.send_error(symbol.name, f"Sell Order Creation Failed: {e};  Action: {action};  Amount: {order_qty}; Price: {order_price}; Effect: {side_effect}; Tipo: {type(e)}; Args: {e.args}; Linea: {e.__traceback__.tb_lineno}")

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
                
            self.can_check_balance = symbol
           
        except Exception as e:
            self.notifier.send_error('Check Filled Order', f"Error: {e}, Name: {symbol.name}, ID: {symbol.open_order_id['orderId']}")
            
        return
    
__all__ = ['Margin_account']
