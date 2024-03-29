
import requests
from sqlalchemy import create_engine, Column, Float, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base

sql_engine = create_engine('mysql+pymysql://server0:donoso850@localhost/bot_database')
sql_base = declarative_base()
session = sessionmaker(bind=sql_engine)
sql_session = session()

def init_database(assets, backup):
    
    tables = {}
    
    for item in assets:
        
        table_name = item
        table = type(table_name, (sql_base,), {
            '__tablename__': table_name,
            'id': Column(Integer, primary_key=True),
            'Date': Column(String(50)),
            'Price': Column(Float)
        })
        tables[table_name] = table
         
    class Table1(sql_base):
        __tablename__ = 'open_tr'
        id = Column(Integer, primary_key=True)
        Date = Column(String(50))
        Name = Column(String(50))
        BuyLevel = Column(Float)
        Amount = Column(Float)
        Cost = Column(Float)
        Profit = Column(Float)
        ProfitUsd = Column(Float)
        Duration = Column(String(50))
    tables['open_tr'] = Table1
  
    class Table2(sql_base):
        __tablename__ = 'status'
        id = Column(Integer, primary_key=True)
        Date = Column(String(50))
        Name = Column(String(50))
        Price = Column(Float)
        Open_point = Column(Float)
        Average_point = Column(Float)
        Average_price = Column(Float)
        Close_point = Column(Float)
        Open_trail_point = Column(Float)
        Average_trail_point = Column(Float)
        Close_trail_point = Column(Float)
    tables['status'] = Table2

    class Table3(sql_base):
        __tablename__ = 'orders'
        id = Column(Integer, primary_key=True)
        Date = Column(String(50))
        Name = Column(String(50))
        Asset = Column(String(50))
        Side = Column(String(50))
        Type = Column(String(50))
        BuyLevel = Column(Float)
        Price = Column(Float)
        Amount = Column(Float)
        Cost = Column(Float)
        Commission = Column(Float)
    tables['orders'] = Table3
        
    class Table4(sql_base):
        __tablename__ = 'transactions'
        id = Column(Integer, primary_key=True)
        Date = Column(String(50))
        Name = Column(String(50))
        Asset = Column(String(50))
        Side = Column(String(50))
        BuyLevel = Column(Float)
        Cost = Column(Float)
        Profit = Column(Float)
        ProfitUsd = Column(Float)
        Commission = Column(Float)
        Duration = Column(String(50))
    tables['transactions'] = Table4
    
    class Table5(sql_base):
        __tablename__ = 'output'
        id = Column(Integer, primary_key=True)
        Date = Column(String(50))
        Type = Column(String(50))
        Asset = Column(String(50))
        Side = Column(String(50))
        Content = Column(String(1000))
    tables['output'] = Table5
    
    class Table6(sql_base):
        __tablename__ = 'nav'
        id = Column(Integer, primary_key=True)
        Date = Column(String(50))
        Nav = Column(Float)
        Bnb_nav = Column(Float)
    tables['nav'] = Table6
    
    class Table7(sql_base):
        __tablename__ = 'margin'
        id = Column(Integer, primary_key=True)
        Date = Column(String(50))
        Margin = Column(Float)
    tables['margin'] = Table7
    
    class Table8(sql_base):
        __tablename__ = 'funds'
        id = Column(Integer, primary_key=True)
        Date = Column(String(50))
        Funds = Column(Float)
        Long_funds = Column(Float)
        Short_funds = Column(Float)
    tables['funds'] = Table8

    class Table9(sql_base):
        __tablename__ = 'open_orders'
        id = Column(Integer, primary_key=True)
        Date = Column(String(50))
        Asset = Column(String(50))
        Side = Column(String(50))
        Price = Column(Float)
        Quantity = Column(Float)
        orderId = Column(Float)
    tables['open_orders'] = Table9

    class Table10(sql_base):
        __tablename__ = 'symbols'
        id = Column(Integer, primary_key=True)
        Name = Column(String(50))
        Drop = Column(Float)
        Profit = Column(Float)
        K = Column(Float)
        Buy_trail = Column(Float)
        Sell_trail = Column(Float)
        Level = Column(Float)
        Pond = Column(Float)
        Switch = Column(String(50))
        Symbol_status = Column(String(50))
        Can_open = Column(String(50))
        Can_average = Column(String(50))
        Can_close = Column(String(50))
        Can_open_trail = Column(String(50))
        Can_average_trail = Column(String(50))
        Can_close_trail = Column(String(50))
    tables['symbols'] = Table10
    
    class Table11(sql_base):
        __tablename__ = 'ponderation'
        id = Column(Integer, primary_key=True)
        Date = Column(String(50))
        Name = Column(String(50))
        Long_ratio = Column(Float)
        Short_ratio = Column(Float)
    tables['ponderation'] = Table11
    
    class Table12(sql_base):
        __tablename__ = 'balances'
        id = Column(Integer, primary_key=True)
        Date = Column(String(50))
        Asset = Column(String(50))
        Base_balance = Column(Float)
        Base_t_balance = Column(Float)
        Base_loan = Column(Float)
        Asset_balance = Column(Float)
        Asset_t_balance = Column(Float)
        Asset_loan = Column(Float)
        Correction = Column(String(50))
        Action = Column(String(50))
    tables['balances'] = Table12
    
    if backup == True:
        print('database charged')
        requests.post('https://api.telegram.org/bot' + '6332743294:AAFKcqzyfKzXAPSGhR6eTKLPMyx0tpCzeA4' + '/sendMessage', data={'chat_id': '-1002023987289', 'text': 'Backup charged', 'parse_mode': 'HTML'})

    else:
        sql_base.metadata.drop_all(sql_engine)
        sql_base.metadata.create_all(sql_engine)
        print('Database files initialized')
        requests.post('https://api.telegram.org/bot' + '6332743294:AAFKcqzyfKzXAPSGhR6eTKLPMyx0tpCzeA4' + '/sendMessage', data={'chat_id': '-1002023987289', 'text': 'Database initialized', 'parse_mode': 'HTML'})

    return tables