
import numpy as np
from datetime import datetime
import math
from binance.client import Client
from bot_database import sql_session
import traceback
from sqlalchemy import exc

class Margin_account():
    
    def __init__(self, notifier) -> None:
        
        self.notifier = notifier
        self.base_coin = 'USDT'
        self.assets = []
        self.available_funds = 0
        self.max_leverage = 3
        self.max_leverage_funds = self.available_funds * self.max_leverage
        self.indiv_max_leverage_funds = self.max_leverage_funds/27
        self.initial_amount = 11
        
        self.nav = 0
        self.margin = 999
        self.funds = 0
        self.long_acc = 0
        self.short_acc = 0
        
        self.balances = {}
        self.loans = {}
        self.t_balances = {self.base_coin:0}
        self.t_loans = {self.base_coin:0}
        
        self.client = Client('HxC4DjBJjOv6lqiDdgnF1c7SW3SYYKnmvRyg1KAW4UY4oa5Ndbz3yAi7Z4TtXky9', 'RwwVEqxVzRmtcxf8sAvMcu6kwz6OxEtxsbcTBDTjgHrsmzqgpCjFcBq0aeW93rEU')
        self.price_precision = {'BTC':2, 'ETH':2, 'BNB':1, 'XRP':4, 'ADA':4, 'LTC':2, 'SOL':2, 'ATOM':3, 'BCH':1, 
                                'DOGE':5, 'DOT':3, 'EOS':3, 'LINK':3, 'TRX':5, 'SHIB':8, 'AVAX':2, 'XLM':4, 'UNI':3, 
                                'ETC':2, 'FIL':3, 'HBAR':4, 'VET':5, 'NEAR':3, 'GRT':4, 'AAVE':2, 'DASH':2, 'MATIC':4, 'USDT':2}
        self.amount_precision = {'BTC':5, 'ETH':4, 'BNB':3, 'XRP':0, 'ADA':1, 'LTC':3, 'SOL':2, 'ATOM':2, 'BCH':3,
                                'DOGE':0, 'DOT':2, 'EOS':1, 'LINK':2, 'TRX':1, 'SHIB':0, 'AVAX':2, 'XLM':0, 'UNI':2, 
                                'ETC':2, 'FIL':2, 'HBAR':0, 'VET':1, 'NEAR':1, 'GRT':0, 'AAVE':3, 'DASH':3, 'MATIC':1, 'USDT':2}
        
        # self.open_order_list = []
    
    def round_decimals_up(self, number, decimals):
        factor = 10 ** decimals
        return math.ceil(number * factor) / factor
    
    def round_decimals_down(self, number, decimals):
        factor = 10 ** decimals
        return math.floor(number * factor) / factor
    
    def get_initial_base_balances(self):
        
        try:
            for item in self.client.get_margin_account()['userAssets']:
                if item['asset'] == self.base_coin:
                    base_balance = float(self.round_decimals_down(float(item['free']), 2))
                    base_loan = float(self.round_decimals_down(float(item['borrowed']) + float(item['interest']), 2))
            self.t_balances[self.base_coin] = base_balance
        except Exception as e:
            print(f"Get initial base balance error: {e}")
            traceback.print_exc()
            self.notifier.register_output('Error', 'general', 'general', 'Get initial base balance error: ' + str(e))
            self.notifier.send_error('General', f"Get initial base balance error: {e}")
        return base_balance, base_loan
    
    def get_base_balances(self):
        
        try:
            for item in self.client.get_margin_account()['userAssets']:
                if item['asset'] == self.base_coin:
                    self.balances[self.base_coin] = self.round_decimals_down(float(item['free']), 2)
                    self.loans[self.base_coin] = self.round_decimals_down(float(item['borrowed']) + float(item['interest']), 2)
        except Exception as e:
            print(f"Get base balance error: {e}")
            traceback.print_exc()
            self.notifier.register_output('Error', 'Base', 'general', 'Get base balance error: ' + str(e))
            self.notifier.send_error('Base', f"Get base balance error: {e}")
        return
    
    def get_asset_balances(self, asset, precision):
        
        try:
            for item in self.client.get_margin_account()['userAssets']:
                if item['asset'] == asset:
                    self.balances[asset] = self.round_decimals_down(float(item['free']), precision)
                    self.loans[asset] = self.round_decimals_down(float(item['borrowed']) + float(item['interest']), precision)
        except Exception as e:
            print(f"Get asset balance error: {e}")
            traceback.print_exc()
            self.notifier.register_output('Error', asset, 'general', 'Get asset balance error: ' + str(e))
            self.notifier.send_error(asset, f"Get asset balance error: {e}")
        return
    
    def get_balances(self):
        for asset in self.assets:
            self.get_asset_balances(asset, self.amount_precision[asset])
            self.get_base_balances(asset)
        return
    
    def check_balances(self, time, action):
        
        for asset in self.assets:
            self.get_balances()
           
            real = self.balances[self.base_coin]
            teor = self.t_balances[self.base_coin]
            diff = (abs(teor)/abs(real) - 1)*100
            diff_usd = teor - real
            
            if diff > 5 and abs(diff_usd) > 10:
                self.notifier.send_error(asset, 'Balances unmached: REAL: ' + str(round(self.balances[asset], self.amount_precision[asset])) + '\n' + 'TEORETHICAL: ' + str(round(self.t_balances[asset], self.amount_precision[asset])) + '\n' + ' DIFF USDT: ' + str(round(diff_usd, 2)))
        
            new_row = self.notifier.tables['balances'](Date=str(time), Asset = asset, Base_balance = self.balances[self.base_coin], Base_t_balance = self.t_balances[self.base_coin], Base_loan = self.loans[self.base_coin], Asset_balance = self.balances[asset], Asset_t_balance = self.t_balances[asset], Asset_loan = self.loans[asset], Action = action)
            sql_session.add(new_row)
        try:
            sql_session.commit()
        except exc.OperationalError as e:
            self.notifier.send_error('NAV Commit', f"Error de conexión a la base de datos: {e}")
            sql_session.rollback()       
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
    
    def create_buy_order(self, symbol, buy_amount_0, price, action):
        
        buy_amount = self.check_funds(buy_amount_0*price, 'BUY', price)
        
        if buy_amount > 0:
            order_qty = self.round_decimals_up(max(buy_amount, self.initial_amount/price), self.amount_precision[symbol.asset])
            order_price = round(price, self.price_precision[symbol.asset])
    
            try:
                self.get_asset_balances(symbol.asset, self.amount_precision[symbol.asset])
    
                if self.loans[symbol.asset] > 0:
                    buy_open_order = self.client.create_margin_order(symbol=symbol.tic, side='BUY', type='STOP_LOSS_LIMIT', quantity=order_qty, price=order_price, stopPrice=order_price, sideEffectType='AUTO_REPAY', timeInForce='GTC')
                else:
                    buy_open_order = self.client.create_margin_order(symbol=symbol.tic, side='BUY', type='STOP_LOSS_LIMIT', quantity=order_qty, price=order_price, stopPrice=order_price, sideEffectType='MARGIN_BUY', timeInForce='GTC')
                
                buy_open_order['action'] = action
                symbol.open_order_id = buy_open_order
    
                check = True
    
            except Exception as e:
                self.notifier.register_output('Error', symbol.asset, symbol.side, 'Buy Order Creation Failed: ' + str(e))
                self.notifier.send_error(symbol.name, f"Buy Order Creation Failed: {e}")
                check = False
        else:
            check = True

        return check
    
    def create_sell_order(self, symbol, buy_amount_0, price, action):
        
        buy_amount = self.check_funds(buy_amount_0*price, 'SELL', price)
        
        if buy_amount > 0:
            order_qty = self.round_decimals_down(max(buy_amount, self.initial_amount/price), self.amount_precision[symbol.asset])
            order_price = round(price, self.price_precision[symbol.asset])
    
            try:
                self.get_base_balances(symbol.asset)
                
                if self.loans[self.base_coin] > 0:
                    sell_open_order = self.client.create_margin_order(symbol=symbol.tic, side='SELL', type='STOP_LOSS_LIMIT', quantity=order_qty, price=order_price, stopPrice=order_price, sideEffectType='AUTO_REPAY', timeInForce='GTC')
                else:
                    sell_open_order = self.client.create_margin_order(symbol=symbol.tic, side='SELL', type='STOP_LOSS_LIMIT', quantity=order_qty, price=order_price, stopPrice=order_price, sideEffectType='MARGIN_BUY', timeInForce='GTC')
    
                sell_open_order['action'] = action
                symbol.open_order_id = sell_open_order
    
                check = True

            except Exception as e:
                self.notifier.register_output('Error', symbol.asset, symbol.side, 'Sell Order Creation Failed: ' + str(e))
                self.notifier.send_error(symbol.name, f"Sell Order Creation Failed: {e}")
                check = False
        else:
            check = False

        return check
    
    def check_partial_order(self, symbol):
        
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
                
        symbol.open_amount_list = np.append(symbol.open_amount_list, [total_amount*average_price])
        symbol.acc = np.sum([symbol.open_amount_list])
        symbol.open_asset_amount_list = np.append(symbol.open_asset_amount_list, [total_amount])
        symbol.asset_acc = np.sum([symbol.open_asset_amount_list])
        symbol.open_price_list = np.append(symbol.open_price_list, [average_price])
        symbol.average_price = np.dot(symbol.open_price_list, symbol.open_asset_amount_list)/symbol.asset_acc

        return total_amount, average_price
    
    def check_filled_order(self, symbol):
        
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

        if order['action'] == 'OPEN':
            symbol.open_order(date, average_price, total_amount, total_commission)
        elif order['action'] == 'AVERAGE':
            symbol.average_order(date, average_price, total_amount, total_commission)
        elif order['action'] == 'CLOSE':
            symbol.close_order(date, average_price, total_amount, total_commission)
            
        return
    
__all__ = ['Margin_account']
