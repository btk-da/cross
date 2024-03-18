
from datetime import datetime
from bot_symbol_long import Symbol_long
from bot_symbol_short import Symbol_short
from bot_database import sql_session, sql_base, sql_engine
from sqlalchemy import delete, exc, Column, Float, Integer, String, update
import traceback
import pickle
from binance.exceptions import BinanceAPIException


class Symbol_combi(object):
        
    def __init__(self) -> None:
                
        self.symbol_list = []
        self.account = []
        self.engine_working = True
        self.wr_list = {'GENERAL': {'Long':0, 'Short':0}}
        
    def add_symbols(self, symbols):
        
        assets = []
        
        for params in symbols:
            if params['drop'] > 0:
                symbol = Symbol_long(params, self)
            elif params['drop'] < 0:
                symbol = Symbol_short(params, self)
                self.wr_list[symbol.nick] = {'Long':0, 'Short':0}

            try:
                symbol.price = float(self.account.client.get_symbol_ticker(symbol=symbol.tic)['price'])
            except Exception as e:
                self.account.notifier.register_output('Error', symbol.asset, symbol.side, 'Initial price reading error: ' + str(e))
                self.account.notifier.send_error(symbol.name, 'Initial price reading error: ' + str(e))
            self.account.get_asset_balances(symbol.asset)
            assets.append(symbol.asset)
            self.symbol_list.append(symbol)
            self.account.notifier.register_output('Info', symbol.asset, symbol.side, 'Symbols added')

        self.account.assets = list(set(assets))
        
        for asset in self.account.assets:
            self.account.have_open_order[asset] = {'Long':False, 'Short':False}
        print('Symbols added')
        
        return
    
    def add_new_symbol(self, inputs):
                
        for params in inputs:
            if params['drop'] > 0:
                symbol = Symbol_long(params, self)
            elif params['drop'] < 0:
                symbol = Symbol_short(params, self)
                self.wr_list[symbol.nick] = {'Long':0, 'Short':0}

            try:
                symbol.price = float(self.account.client.get_symbol_ticker(symbol=symbol.tic)['price'])
            except Exception as e:
                self.account.notifier.register_output('Error', symbol.asset, symbol.side, 'Initial price reading error: ' + str(e))
                self.account.notifier.send_error(symbol.name, 'Initial price reading error: ' + str(e))
            
            if symbol.asset not in self.account.assets:
                self.account.assets.append(symbol.asset)
                nueva_tabla = type('NuevaTabla', (sql_base,), {
                    '__tablename__': symbol.asset,
                    'id': Column(Integer, primary_key=True),
                    'Date': Column(String(50)),
                    'Price': Column(Float)})
                self.account.notifier.tables[symbol.asset] = nueva_tabla
                sql_base.metadata.create_all(sql_engine)
                self.account.t_balances[symbol.asset] = 0
                self.account.t_loans[symbol.asset] = 0
                self.account.balances[symbol.asset] = 0
                self.account.loans[symbol.asset] = 0
                
            self.account.get_asset_balances(symbol.asset)
            self.symbol_list.append(symbol)
            self.account.notifier.register_output('Info', symbol.asset, symbol.side, 'Symbols added')
            time = datetime(datetime.now().year, datetime.now().month, datetime.now().day, datetime.now().hour, datetime.now().minute, datetime.now().second)
            symbol.open_order(time, symbol.price, self.account.initial_amount/symbol.price, 0)
     
        self.account.assets = list(set(self.account.assets))
        print('Symbols added')
        
        return
    
    def init_params(self, backup): 
        
        asset_list = []
        long_acc = 0
        short_acc = 0
        for symbol in self.symbol_list:
            asset_list.append(symbol.asset)
            if symbol.side == 'Long':
                long_acc = long_acc + symbol.acc
            elif symbol.side == 'Short':
                short_acc = short_acc + symbol.acc
        
        self.account.assets = list(set(asset_list))
        self.account.long_acc = long_acc
        self.account.short_acc = short_acc
        self.account.funds = short_acc - long_acc
        
        for asset in self.account.assets:
            self.account.t_balances[asset] = 0
            self.account.t_loans[asset] = 0
            
        for i in self.account.assets:
            self.account.get_asset_balances(i)
        self.account.get_base_balances()

        self.account.t_balances[self.account.base_coin] = self.account.balances[self.account.base_coin]
        self.account.available_funds = self.account.balances[self.account.base_coin]
        self.account.max_leverage_funds = self.account.available_funds * self.account.max_leverage
        time = datetime(datetime.now().year, datetime.now().month, datetime.now().day, datetime.now().hour, datetime.now().minute, datetime.now().second)
        print('Base balance: ', self.account.balances[self.account.base_coin])
        self.account.notifier.register_output('Info', 'general', 'general', 'Base balance: ' + str(self.account.balances[self.account.base_coin]))
        print('Max funds: ', round(self.account.max_leverage_funds))
        self.account.notifier.register_output('Info', 'general', 'general', 'Max funds: ' + str(round(self.account.max_leverage_funds)))
        
        if backup == False:
            for i in self.symbol_list:
                price = float(self.account.client.get_symbol_ticker(symbol=i.tic)['price'])
                i.open_order(time, price, self.account.initial_amount/price, 0)
                                                                               
        return
    
    def read_open_orders(self):
        
        restart_open_orders = delete(self.account.notifier.tables['open_orders'])
        sql_session.execute(restart_open_orders)
        # restart_open_order_bool = delete(self.account.notifier.tables['open_order_bool'])
        # sql_session.execute(restart_open_order_bool)
        sql_session.commit()
        
        time = datetime(datetime.now().year, datetime.now().month, datetime.now().day, datetime.now().hour, datetime.now().minute, datetime.now().second)

        for symbol in self.symbol_list:
            if symbol.side == 'Long':
                open_orders = self.account.client.get_open_margin_orders(symbol=symbol.tic)
                
                for order in open_orders:
                    new_row = self.account.notifier.tables['open_orders'](Date=str(time), Asset=symbol.asset, Side=order['side'], Price=float(order['price']), Quantity = float(order['origQty']), orderId = order['orderId'])
                    sql_session.add(new_row)
        
        # for i in self.account.have_open_order:
        #     new_row = self.account.notifier.tables['open_order_bool'](Date=str(time), Asset=i, Long=self.account.have_open_order[i]['Long'], Short=self.account.have_open_order[i]['Short'])
        #     sql_session.add(new_row)
            
        sql_session.commit()
        
        return
    
    def update_symbol_status(self, time):
        
        time = datetime(datetime.now().year, datetime.now().month, datetime.now().day, datetime.now().hour, datetime.now().minute, datetime.now().second)

        restart_status = delete(self.account.notifier.tables['status'])
        sql_session.execute(restart_status)
        restart_open_tr = delete(self.account.notifier.tables['open_tr'])
        sql_session.execute(restart_open_tr)
        sql_session.commit()

        with open("symbols.pickle", "rb") as f:
            symbols_backup = pickle.load(f)
            
        for name in symbols_backup.keys():
            symbol = symbols_backup[name]
            new_row = self.account.notifier.tables['status'](Date=str(time), Name=symbol['name'], Drop=symbol['drop'], Profit=symbol['profit'], K=symbol['k'], Buy_trail=symbol['buy_trail'], Sell_trail=symbol['sell_trail'], Level=symbol['level'], Pond=symbol['pond'], Switch=symbol['switch'], Symbol_status=symbol['status'], Can_open=symbol['can_open'], Can_average=symbol['can_average'], Can_close=symbol['can_close'], Can_open_trail=symbol['can_open_trail'], Can_average_trail=symbol['can_average_trail'], Can_close_trail=symbol['can_close_trail'], Price=symbol['price'], Open_point=symbol['open_price'], Average_point=symbol['average_point'], Average_price=symbol['average_price'], Close_point=symbol['close_point'], Open_trail_point=symbol['open_trail_point'], Average_trail_point=symbol['average_trail_point'], Close_trail_point=symbol['close_trail_point'])
            sql_session.add(new_row)
            new_row = self.account.notifier.tables['open_tr'](Date=str(time), Name=symbol['name'], BuyLevel=symbol['buy_level'], Amount=round(symbol['asset_acc'], 4), Cost=round(symbol['acc']), Profit=round(symbol['live_profit']*100, 2), ProfitUsd=round(symbol['live_profit']*symbol['acc'], 2), Duration=symbol['duration'])
            sql_session.add(new_row)
                        
        try:
            sql_session.commit()
        except exc.OperationalError as e:
            self.account.notifier.send_error(symbol.name, f"Error de conexión a la base de datos: {e}")
            sql_session.rollback()
            
        return
    
    def update_balances(self):
        
        time = datetime(datetime.now().year, datetime.now().month, datetime.now().day, datetime.now().hour, datetime.now().minute, datetime.now().second)
        restart_balances = delete(self.account.notifier.tables['balances'])
        sql_session.execute(restart_balances)
        sql_session.commit()
        
        self.account.get_all_balances()
        self.account.teor_balances = {}
        
        for symbol in self.symbol_list:
            
            if symbol.side == 'Long':
                self.account.teor_balances[symbol.asset] = symbol.asset_acc
            else:
                self.account.teor_balances[symbol.asset] = self.account.teor_balances[symbol.asset] - symbol.asset_acc
                
                # price = float(self.account.client.get_symbol_ticker(symbol=symbol.tic)['price'])
                # if self.account.balances[symbol.asset]*price <= 9:
                #     asset_balance = 0
                # else:
                #     asset_balance = self.account.balances[symbol.asset]
                    
                # if abs(self.account.teor_balances[symbol.asset])*price <= 9:
                #     asset_balance_t = 0
                # else:
                #     asset_balance_t = self.account.teor_balances[symbol.asset]
                
                # if asset_balance_t > 0:
                #     diff = abs(self.account.teor_balances[symbol.asset] - self.account.balances[symbol.asset])
                #     diff_usdt = diff * price
                # else:
                #     diff = abs(abs(asset_balance_t) - self.account.loans[symbol.asset])
                #     diff_usdt = diff * price
                 
                # if diff_usdt >= 10:
                #     open_orders = self.account.client.get_open_margin_orders(symbol=symbol.tic)
                #     if len(open_orders) == 0 and self.account.have_open_order[symbol.asset]['Long'] == False and self.account.have_open_order[symbol.asset]['Short'] == False:
                #         self.account.notifier.send_error('Check balance', f"Correccion de balances: Symbol: {symbol.name}, Diff: {diff_usdt}")
                #         self.account.check_balances(symbol, price)

                # new_row = self.account.notifier.tables['balances'](Date=str(time), Asset = symbol.asset, Balance = asset_balance, T_balance = asset_balance_t, Loan = self.account.loans[symbol.asset], Diff_usdt = round(diff_usdt), Diff = diff, Price = price, Long = self.account.have_open_order[symbol.asset]['Long'], Short = self.account.have_open_order[symbol.asset]['Short'])
                # sql_session.add(new_row)
                real, teor, loan, diff_usdt, diff, price = self.account.check_balances(symbol)
                new_row = self.account.notifier.tables['balances'](Date=str(time), Asset = symbol.asset, Balance = real, T_balance = teor, Loan = loan, Diff_usdt = round(diff_usdt), Diff = diff, Price = price, Long = self.account.have_open_order[symbol.asset]['Long'], Short = self.account.have_open_order[symbol.asset]['Short'])
                sql_session.add(new_row)

        sql_session.commit()
        
        # if len(self.account.can_check_balance) != 0:
        #     self.account.check_balances(self.account.can_check_balance)
        #     self.account.can_check_balance = []

        return
    
    def update_open_tr(self):
        
        time = datetime(datetime.now().year, datetime.now().month, datetime.now().day, datetime.now().hour, datetime.now().minute, datetime.now().second)
        self.account.calculate_nav(time)
        
        for symbol in self.symbol_list:
            
            try:
                time = datetime(datetime.now().year, datetime.now().month, datetime.now().day, datetime.now().hour, datetime.now().minute, datetime.now().second)
    
                try:
                    price = float(self.account.client.get_symbol_ticker(symbol=symbol.tic)['price'])
                except Exception as e:
                    self.account.notifier.send_error(symbol.name, 'Price reading error: ' + str(e))
                    traceback.print_exc()
                    price = symbol.price
                
                if price > symbol.price*(1 + 0.1):
                    print('Last Price: ', symbol.price, 'Higher price', price)
                elif price < symbol.price*(1 - 0.1):
                    print('Last Price: ', symbol.price, 'Lower price', price)
                else:
                    symbol.price = float(price)
            
                new_row = self.account.notifier.tables[str(symbol.asset)](Date=str(time), Price=price)
                sql_session.add(new_row)
                sql_session.commit()
                symbol.logic(time, price)
                
                self.account.notifier.register_output('Update', symbol.asset, symbol.name, 'Symbols Updated')
                
            except Exception as e:
                self.account.notifier.send_error('General', f'SYMBOL UPDATING ERROR: {e}; Tipo: {type(e)}; Args: {e.args}; Linea: {e.__traceback__.tb_lineno}')
             
        self.read_open_orders()
        self.update_symbol_status(time)
        self.update_balances()
        self.account.notifier.register_output('Info', 'general', 'general', 'Symbols updated')
        return

__all__ = ['Symbol_combi']

    