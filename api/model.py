# 데이터 베이스 테이블 정의
from sqlalchemy import Column,Integer,String,ForeignKey
from database import Base

class User(Base):  # 테이블  Base를 상속받아야만  sqlite 테이블 생성  
    __tablename__ ='users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String,unique=True,index=True)
    email = Column(String, unique=True,index=True)
    password = Column(String)  # 일단 보안은 나중에.
# 상품테이블
class Product(Base):
    __tablename__ ='products'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String,unique=True,index=True)
    price = Column(Integer)
# 장바구니테이블
class Cart(Base):
    __tablename__ ='cart'
    id = Column(Integer, primary_key=True, index=True)    
    user_id = Column(Integer,ForeignKey('users.id'))
    product_id = Column(Integer,ForeignKey('products.id'))
    quantity = Column(Integer)

# 주문
class Order(Base):
    __tablename__ ='orders'
    id = Column(Integer, primary_key=True, index=True)    
    user_id = Column(Integer,ForeignKey('users.id'))
    product_id = Column(Integer,ForeignKey('products.id'))
    quantity = Column(Integer)