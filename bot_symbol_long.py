
import numpy as np
import requests
from bot_database import sql_session
from sqlalchemy import exc, delete

class Symbol_long(object):

    def __init__(self, params, master) -> None:
        
        self.master = master
        self.params = params
        self.drop = params['drop']
        self.profit = params['profit']
        self.k = params['k']
        self.buy_trail = params['buy_trail']
        self.sell_trail = params['sell_trail']
        self.level = params['level']
        self.pond = params['pond']   
        self.asset = params['asset']
        self.tic = self.asset + self.master.account.base_coin
        self.name = self.asset + '--L'
        self.side = 'Long'
        self.nick = str(abs(self.drop)) + str(self.profit) + str(self.k) + self.asset

        self.symbol_status = True
        self.switch = True
        self.status = False
        self.can_open = False
        self.can_average = False
        self.can_close = False
        self.can_open_trail = False
        self.can_average_trail = False
        self.can_close_trail = False
    
        self.open_price = []
        self.open_time = []
        self.close_time = []
        self.duration = '0'
        self.acc = 0
        self.open_amount_list = np.array([])
        self.open_price_list = np.array([])
        self.open_asset_amount_list = np.array([])
        self.asset_acc = 0     
        self.average_price = 0
        self.average_point = 0.0000000001
        self.close_point = 1000000000
        self.buy_level = 0
        self.price = []
        self.live_profit = 0
        
        self.base_open_trail = 0
        self.base_average_trail = 0
        self.base_close_trail = 0
        self.open_trail_point = 0
        self.average_trail_point = 0
        self.close_trail_point = 0
        
        self.interp_range = np.array(np.arange(0,50),dtype='float64')
        self.buy_distribution = np.cumsum(self.k**np.array(np.arange(0,50)) * self.master.account.initial_amount).astype('float64')
        
        self.commission = 0
        self.open_order_id = []
        self.last_buy_price = []
        
    def trading_points(self):
        
        self.average_point = self.last_buy_price * (1 - self.drop/100)
        self.close_point = self.average_price * (1 + (self.profit+self.sell_trail)/100)
        return
        
    def open_trailing(self, time, price):
        
        if len(self.open_order_id) != 0:
            if price < self.base_open_trail:
                self.base_open_trail = price
                self.open_trail_point = self.base_open_trail*(1 + self.buy_trail/100)
    
                open_order = self.master.account.client.get_margin_order(symbol=self.open_order_id['symbol'], orderId=self.open_order_id['orderId'])
    
                if open_order['status'] == 'FILLED':
                    self.master.account.check_filled_order(self)
    
                elif open_order['status'] == 'NEW':
                    cancel = self.master.account.client.cancel_margin_order(symbol=self.tic, orderId=open_order['orderId'])
                    if cancel['status'] == 'CANCELED':
                        order_id_to_delete = self.open_order_id['orderId']
                        delete_statement = delete(self.master.account.notifier.tables['open_orders']).where(self.master.account.notifier.tables['open_orders'].orderId == order_id_to_delete)
                        sql_session.execute(delete_statement)
                        sql_session.commit()
                        self.open_order_id = []
                        buy_amount = np.interp(0, self.interp_range, self.buy_distribution)
                        check = self.master.account.create_buy_order(self, buy_amount/self.open_trail_point, self.open_trail_point, 'OPEN', price)
    
                elif open_order['status'] == 'PARTIALLY FILLED':
                    cancel = self.master.account.client.cancel_margin_order(symbol=self.tic, orderId=open_order['orderId'])
                    if cancel['status'] == 'CANCELED':
                        order_id_to_delete = self.open_order_id['orderId']
                        delete_statement = delete(self.master.account.notifier.tables['open_orders']).where(self.master.account.notifier.tables['open_orders'].orderId == order_id_to_delete)
                        sql_session.execute(delete_statement)
                        sql_session.commit()
                        self.open_order_id = []
                        partial_amount, partial_price = self.master.account.check_partial_order(self)
                        
                        self.open_amount_list = np.append(self.open_amount_list, [partial_amount*partial_price])
                        self.acc = np.sum([self.open_amount_list])
                        self.open_asset_amount_list = np.append(self.open_asset_amount_list, [partial_amount])
                        self.asset_acc = np.sum([self.open_asset_amount_list])
                        self.open_price_list = np.append(self.open_price_list, [partial_price])
                        self.average_price = np.dot(self.open_price_list, self.open_asset_amount_list)/self.asset_acc
                        self.master.account.funds = self.master.account.funds - partial_amount*partial_price
                        self.master.account.long_acc = self.master.account.long_acc + partial_amount*partial_price
                        
                        buy_amount = np.interp(0, self.interp_range, self.buy_distribution)
                        check = self.master.account.create_buy_order(self, (buy_amount/self.open_trail_point - partial_amount), self.open_trail_point, 'OPEN', price)
        else:
            self.can_open_trail = False
            self.can_open = True
        return
        
    def open_order(self, time, price, amount, comision):
        
        self.open_time = time
        self.open_price = price

        self.open_amount_list = np.append(self.open_amount_list, [amount*price])
        self.acc = np.sum([self.open_amount_list])
        self.open_asset_amount_list = np.append(self.open_asset_amount_list, [amount])
        self.asset_acc = np.sum([self.open_asset_amount_list])
        self.open_price_list = np.append(self.open_price_list, [price])
        self.average_price = np.dot(self.open_price_list, self.open_asset_amount_list)/self.asset_acc
        
        self.master.account.funds = self.master.account.funds - amount*price
        self.master.account.long_acc = self.master.account.long_acc + amount*price
        self.master.account.t_balances[self.asset] = self.master.account.t_balances[self.asset] + amount
        self.master.account.t_balances[self.master.account.base_coin] = self.master.account.t_balances[self.master.account.base_coin] - amount*price - comision
               
        self.average_point = price * (1 - self.drop/100)
        self.close_point = self.average_price * (1 + (self.profit+self.sell_trail)/100)
    
        self.status = True
        self.can_average = True
        self.can_close = True
        self.can_open_trail = False
        self.can_open = False
        
        indiv_pond = self.acc/self.master.account.max_leverage_funds*100
        # gen_pond = self.master.account.long_acc/self.master.account.max_leverage_funds*100
        
        self.master.wr_list[self.nick][self.side] = indiv_pond
        # self.master.wr_list['GENERAL'][self.side] = gen_pond
        new_row = self.master.account.notifier.tables['ponderation'](Date=str(time), Name=self.name, Long_ratio=self.master.wr_list[self.nick]['Long'], Short_ratio=self.master.wr_list[self.nick]['Short'])
        # new_row = self.master.account.notifier.tables['ponderation'](Date=str(time), Name='GENERAL', Long_ratio=self.master.wr_list['GENERAL']['Long'], Short_ratio=self.master.wr_list['GENERAL']['Short'])
        sql_session.add(new_row)
        sql_session.commit()
        
        self.master.account.notifier.send_open_order_filled(price, amount, self)
        
        new_row = self.master.account.notifier.tables['funds'](Date=str(time), Funds=self.master.account.funds, Long_funds=self.master.account.long_acc, Short_funds=self.master.account.short_acc)
        sql_session.add(new_row)
        new_row = self.master.account.notifier.tables['orders'](Date=str(time), Name=self.name, Asset=self.asset, Side=self.side, Type='Buy', BuyLevel=self.buy_level, Price=price, Amount=amount, Cost=round(self.acc), Commission=comision)
        sql_session.add(new_row)
        try:
            sql_session.commit()
        except exc.OperationalError as e:
            print(f"Error de conexión a la base de datos: {e}")
            self.master.account.notifier.send_error(self.name, f"Error de conexión a la base de datos: {e}")
            sql_session.rollback()
        
        self.last_buy_price = price

        return
    
    def average_trailing(self, time, price):

        if len(self.open_order_id) != 0:
            if price < self.base_average_trail:
                self.base_average_trail = price
                self.average_trail_point = self.base_average_trail*(1 + self.buy_trail/100)
                
                open_order = self.master.account.client.get_margin_order(symbol=self.open_order_id['symbol'], orderId=self.open_order_id['orderId'])
                
                if open_order['status'] == 'FILLED':
                    self.master.account.check_filled_order(self)
    
                elif open_order['status'] == 'NEW':
                    cancel = self.master.account.client.cancel_margin_order(symbol=self.tic, orderId=open_order['orderId'])
                    if cancel['status'] == 'CANCELED':
                        order_id_to_delete = self.open_order_id['orderId']
                        delete_statement = delete(self.master.account.notifier.tables['open_orders']).where(self.master.account.notifier.tables['open_orders'].orderId == order_id_to_delete)
                        sql_session.execute(delete_statement)
                        sql_session.commit()
                        self.open_order_id = []
                        buy_amount = self.calculate_interp()
                        check = self.master.account.create_buy_order(self, buy_amount/self.average_trail_point, self.average_trail_point, 'AVERAGE', price)
                
                elif open_order['status'] == 'PARTIALLY FILLED':
                    cancel = self.master.account.client.cancel_margin_order(symbol=self.tic, orderId=open_order['orderId'])
                    if cancel['status'] == 'CANCELED':
                        order_id_to_delete = self.open_order_id['orderId']
                        delete_statement = delete(self.master.account.notifier.tables['open_orders']).where(self.master.account.notifier.tables['open_orders'].orderId == order_id_to_delete)
                        sql_session.execute(delete_statement)
                        sql_session.commit()
                        self.open_order_id = []
                        partial_amount, partial_price = self.master.account.check_partial_order(self)
                        
                        self.open_amount_list = np.append(self.open_amount_list, [partial_amount*partial_price])
                        self.acc = np.sum([self.open_amount_list])
                        self.open_asset_amount_list = np.append(self.open_asset_amount_list, [partial_amount])
                        self.asset_acc = np.sum([self.open_asset_amount_list])
                        self.open_price_list = np.append(self.open_price_list, [partial_price])
                        self.average_price = np.dot(self.open_price_list, self.open_asset_amount_list)/self.asset_acc
                        self.master.account.funds = self.master.account.funds - partial_amount*partial_price
                        self.master.account.long_acc = self.master.account.long_acc + partial_amount*partial_price
                        
                        buy_amount = self.calculate_interp()           
                        check = self.master.account.create_buy_order(self, (buy_amount/self.average_trail_point - partial_amount), self.average_trail_point, 'AVERAGE', price) 
        else:
            self.can_average_trail = False
            self.can_average = True
            
        return

    def average_order(self, time, price, amount, comision):
        
        self.open_amount_list = np.append(self.open_amount_list, [amount*price])
        self.acc = np.sum([self.open_amount_list])
        self.open_asset_amount_list = np.append(self.open_asset_amount_list, [amount])
        self.asset_acc = np.sum([self.open_asset_amount_list])
        self.open_price_list = np.append(self.open_price_list, [price])
        self.average_price = np.dot(self.open_price_list, self.open_asset_amount_list)/self.asset_acc
        
        self.master.account.funds = self.master.account.funds - amount*price
        self.master.account.long_acc = self.master.account.long_acc + amount*price
        self.master.account.t_balances[self.asset] = self.master.account.t_balances[self.asset] + amount
        self.master.account.t_balances[self.master.account.base_coin] = self.master.account.t_balances[self.master.account.base_coin] - amount*price - comision
        
        total_drop = (1 - price/self.open_price) * 100
        self.buy_level = round(total_drop / self.drop, 1)
        last_drop = (1 - price/self.last_buy_price) * 100
    
        self.average_point = price * (1 - self.drop/100)
        self.close_point = self.average_price * (1 + (self.profit+self.sell_trail)/100) 

        self.can_average = True
        self.can_average_trail = False
        
        self.master.account.notifier.send_average_order_filled(price, amount, self, last_drop)
        
        new_row = self.master.account.notifier.tables['funds'](Date=str(time), Funds=self.master.account.funds, Long_funds=self.master.account.long_acc, Short_funds=self.master.account.short_acc)
        sql_session.add(new_row)
        new_row = self.master.account.notifier.tables['orders'](Date=str(time), Name=self.name, Asset=self.asset, Side=self.side, Type='Buy', BuyLevel=self.buy_level, Price=price, Amount=amount, Cost=round(self.acc), Commission=comision)
        sql_session.add(new_row)
        try:
            sql_session.commit()
        except exc.OperationalError as e:
            print(f"Error de conexión a la base de datos: {e}")
            self.master.account.notifier.send_error(self.name, f"Error de conexión a la base de datos: {e}")
            sql_session.rollback()
            
        self.last_buy_price = price
        
        indiv_pond = self.acc/self.master.account.max_leverage_funds*100
        # gen_pond = self.master.account.long_acc/self.master.account.max_leverage_funds*100
        
        self.master.wr_list[self.nick][self.side] = indiv_pond
        # self.master.wr_list['GENERAL'][self.side] = gen_pond
        new_row = self.master.account.notifier.tables['ponderation'](Date=str(time), Name=self.name, Long_ratio=self.master.wr_list[self.nick]['Long'], Short_ratio=self.master.wr_list[self.nick]['Short'])
        # new_row = self.master.account.notifier.tables['ponderation'](Date=str(time), Name='GENERAL', Long_ratio=self.master.wr_list['GENERAL']['Long'], Short_ratio=self.master.wr_list['GENERAL']['Short'])
        sql_session.add(new_row)
        sql_session.commit()
        
        return
    
    def close_trailing(self, time, price):
        
        if len(self.open_order_id) != 0:
            if price > self.base_close_trail:
                self.base_close_trail = price
                self.close_trail_point = self.base_close_trail*(1 - self.sell_trail/100)
    
                open_order = self.master.account.client.get_margin_order(symbol=self.open_order_id['symbol'], orderId=self.open_order_id['orderId'])
    
                if open_order['status'] == 'FILLED':
                    self.master.account.check_filled_order(self)
    
                elif open_order['status'] == 'NEW':
                    cancel = self.master.account.client.cancel_margin_order(symbol=self.tic, orderId=open_order['orderId'])
                    if cancel['status'] == 'CANCELED':
                        order_id_to_delete = self.open_order_id['orderId']
                        delete_statement = delete(self.master.account.notifier.tables['open_orders']).where(self.master.account.notifier.tables['open_orders'].orderId == order_id_to_delete)
                        sql_session.execute(delete_statement)
                        sql_session.commit()
                        self.open_order_id = []
                        check = self.master.account.create_sell_order(self, self.asset_acc, self.close_trail_point, 'CLOSE', price)
    
                elif open_order['status'] == 'PARTIALLY FILLED':
                    cancel = self.master.account.client.cancel_margin_order(symbol=self.tic, orderId=open_order['orderId'])
                    if cancel['status'] == 'CANCELED':
                        order_id_to_delete = self.open_order_id['orderId']
                        delete_statement = delete(self.master.account.notifier.tables['open_orders']).where(self.master.account.notifier.tables['open_orders'].orderId == order_id_to_delete)
                        sql_session.execute(delete_statement)
                        sql_session.commit()
                        self.open_order_id = []
                        partial_amount, partial_price = self.master.account.check_partial_order(self)
                        
                        self.open_amount_list = np.append(self.open_amount_list, [-partial_amount*partial_price])
                        self.acc = np.sum([self.open_amount_list])
                        self.open_asset_amount_list = np.append(self.open_asset_amount_list, [-partial_amount])
                        self.asset_acc = np.sum([self.open_asset_amount_list])
                        self.open_price_list = np.append(self.open_price_list, [partial_price])
                        self.average_price = np.dot(self.open_price_list, self.open_asset_amount_list)/self.asset_acc
                        
                        self.master.account.funds = self.master.account.funds + partial_amount*partial_price
                        self.master.account.long_acc = self.master.account.long_acc - partial_amount*partial_price
                        check = self.master.account.create_sell_order(self, self.asset_acc, self.close_trail_point, 'CLOSE', price)
        else:
            self.can_close_trail = False
            self.can_close = True
        return

    def close_order(self, time, price, amount, comision):
                
        profit = (price/self.average_price - 1)
        usd_profit = profit * self.acc - self.commission
        self.duration = time - self.open_time
                
        self.master.account.funds = self.master.account.funds + self.acc
        self.master.account.long_acc = self.master.account.long_acc - self.acc
        self.master.account.t_balances[self.asset] = self.master.account.t_balances[self.asset] - amount
        self.master.account.t_balances[self.master.account.base_coin] = self.master.account.t_balances[self.master.account.base_coin] + amount*price - comision
    
        covered = round(((1 - self.last_buy_price/self.open_price) * 100), 2)

        self.master.account.notifier.send_transaction_closed_filled(self, profit, usd_profit, self.commission, price, covered)

        new_row = self.master.account.notifier.tables['funds'](Date=str(time), Funds=self.master.account.funds, Long_funds=self.master.account.long_acc, Short_funds=self.master.account.short_acc)
        sql_session.add(new_row)
        new_row = self.master.account.notifier.tables['orders'](Date=str(time), Name=self.name, Asset=self.asset, Side=self.side, Type='Sell', BuyLevel=self.buy_level, Price=price, Amount=amount, Cost=round(self.acc), Commission=comision)
        sql_session.add(new_row)
        new_row = self.master.account.notifier.tables['transactions'](Date=str(time), Name=self.name, Asset=self.asset, Side=self.side, BuyLevel=self.buy_level, Cost=round(self.acc), Profit=profit*100, ProfitUsd=float(usd_profit), Commission=self.commission, Duration=str(self.duration))
        sql_session.add(new_row)
        try:
            sql_session.commit()
        except exc.OperationalError as e:
            print(f"Error de conexión a la base de datos: {e}")
            self.master.account.notifier.send_error(self.name, f"Error de conexión a la base de datos: {e}")
            sql_session.rollback()
                
        self.open_amount_list = np.array([])
        self.open_price_list = []
        self.open_asset_amount_list = np.array([])
        self.asset_acc = 0
        self.buy_level = 0
        self.acc = 0
        self.duration = '0'
        self.close_point = 1000000000
        self.live_profit = 0
        self.average_price = 0
        self.commission = 0
        
        indiv_pond = self.acc/self.master.account.max_leverage_funds*100
        # gen_pond = self.master.account.long_acc/self.master.account.max_leverage_funds*100
        
        self.master.wr_list[self.nick][self.side] = indiv_pond
        # self.master.wr_list['GENERAL'][self.side] = gen_pond
        new_row = self.master.account.notifier.tables['ponderation'](Date=str(time), Name=self.name, Long_ratio=self.master.wr_list[self.nick]['Long'], Short_ratio=self.master.wr_list[self.nick]['Short'])
        # new_row = self.master.account.notifier.tables['ponderation'](Date=str(time), Name='GENERAL', Long_ratio=self.master.wr_list['GENERAL']['Long'], Short_ratio=self.master.wr_list['GENERAL']['Short'])
        sql_session.add(new_row)
        sql_session.commit()
        
        self.status = False
        self.can_open = True
        self.can_average = False
        self.can_close = False
        self.can_close_trail = False
        
        return

    def logic(self, time, price):

        if self.status:
            self.live_profit = (price/self.average_price - 1)
            self.duration = time - self.open_time

        if len(self.open_order_id) != 0:
            open_order = self.master.account.client.get_margin_order(symbol=self.open_order_id['symbol'], orderId=self.open_order_id['orderId'])
            if open_order['status'] == 'FILLED':
                self.master.account.check_filled_order(self)

        if self.can_open_trail:
            self.open_trailing(time, price)
            
        if self.can_open and self.switch:
            if self.master.wr_list[self.nick]['Short'] >= self.level and self.master.wr_list[self.nick]['Short'] > self.master.wr_list[self.nick]['Long']:
                self.buy_distribution = np.cumsum(self.k**np.array(np.arange(0,50)) * self.master.account.initial_amount).astype('float64') * self.pond
            else:
                self.buy_distribution = np.cumsum(self.k**np.array(np.arange(0,50)) * self.master.account.initial_amount).astype('float64')

            if len(self.open_order_id) != 0:
                self.master.account.client.cancel_margin_order(symbol=self.tic, orderId=self.open_order_id['orderId'])
            self.base_open_trail = price
            self.open_trail_point = self.base_open_trail*(1 + self.buy_trail/100)
            buy_amount = np.interp(0, self.interp_range, self.buy_distribution)
            check = self.master.account.create_buy_order(self, buy_amount/self.open_trail_point, self.open_trail_point, 'OPEN', price)
            if check:
                self.can_open_trail = True
                self.can_open = False
                self.master.account.notifier.send_order_placed('OPEN', self, self.open_trail_point, buy_amount/self.open_trail_point)
            else:
                self.can_open_trail = False
                self.can_open = True
                
        if self.can_average_trail:
            self.average_trailing(time, price)
            
        if price < self.average_point and self.can_average:

            if len(self.open_order_id) != 0:
                self.master.account.client.cancel_margin_order(symbol=self.tic, orderId=self.open_order_id['orderId'])
            self.base_average_trail = price
            self.average_trail_point = self.base_average_trail*(1 + self.buy_trail/100)
            buy_amount = self.calculate_interp()              
            check = self.master.account.create_buy_order(self, buy_amount/self.average_trail_point, self.average_trail_point, 'AVERAGE', price)
            if check:
                self.can_average_trail = True
                self.can_average = False
                self.can_close_trail = False
                self.can_close = True
                self.master.account.notifier.send_order_placed('AVERAGE', self, self.average_trail_point, buy_amount/self.average_trail_point)
            else:
                self.can_average_trail = False
                self.can_average = True
                self.can_close_trail = False
                self.can_close = True

        if self.can_close_trail:
            self.close_trailing(time, price)
            
        if price > self.close_point and self.can_close:
            
            if len(self.open_order_id) != 0:
                self.master.account.client.cancel_margin_order(symbol=self.tic, orderId=self.open_order_id['orderId'])
            self.base_close_trail = price
            self.close_trail_point = self.base_close_trail*(1 - self.sell_trail/100)
            check = self.master.account.create_sell_order(self, self.asset_acc, self.close_trail_point, 'CLOSE', price)
            if check:
                self.can_average_trail = False
                self.can_average = True
                self.can_close_trail = True
                self.can_close = False
                self.master.account.notifier.send_order_placed('CLOSE', self, self.close_trail_point, self.asset_acc)
            else:
                self.can_average_trail = False
                self.can_average = True
                self.can_close_trail = False
                self.can_close = True          
                  
        return
    
    def calculate_interp(self):
        
        total_drop = (1 - self.average_trail_point/self.open_price) * 100
        buy_level = round(total_drop / self.drop, 1)
        buy_amount = np.interp(buy_level, self.interp_range, self.buy_distribution) - self.acc      

        return buy_amount   
    
__all__ = ['Symbol_long']