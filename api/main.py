# FAST API의 메인 서버
from fastapi import FastAPI,HTTPException,Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from model import *
from database import SessionLocal,engin
from schemas import *
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import logging
import sys
from logging.handlers import TimedRotatingFileHandler
import os
from datetime import datetime
import json

# 현재 스크립트의 절대 경로
current_dir = os.path.dirname(os.path.abspath(__file__))
# 프로젝트 루트 디렉토리 (api의 상위 디렉토리)
project_root = os.path.dirname(current_dir)
# 로그 디렉토리 경로
log_dir = os.path.join(project_root, 'logs')

# 로그 디렉토리 생성
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
    print(f'Created log directory at: {log_dir}')

# 로그 파일 경로 설정
log_file = os.path.join(log_dir, 'api.log')
print(f'API Log file will be saved at: {log_file}')

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        # 콘솔 출력
        logging.StreamHandler(sys.stdout),
        # 파일 출력 (날짜별 로테이션)
        TimedRotatingFileHandler(
            filename=log_file,
            when='midnight',  # 매일 자정에 새로운 파일 생성
            interval=1,       # 1일 간격
            backupCount=30,   # 30일치 로그 파일 유지
            encoding='utf-8'
        )
    ]
)

# 로거 설정
logger = logging.getLogger(__name__)
logger.info(f'API Logging initialized. Log directory: {log_dir}')

# Fast api 생성
app = FastAPI()

# CORS(Cross-Origin Resource Sharing) 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins = ["http://127.0.0.1:5000",'http://localhost:5000'], # flask 주소 허용
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)

# 앱을 실행하면 DB에 정의된 모든 테이블을 생성
Base.metadata.create_all(bind=engin)

def get_db():
    db = SessionLocal()  # 새션 객체  생성
    try:
        yield db # 종속된 함수에 세션 주입
    finally:
        db.close()  # 요청이 끝나면 자동으로 세션 종료


from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import FastAPI, Request

# 템플릿 디렉토리 설정
# pip install jinja2
# fastapi 방식으로 화면을 랜더랑 사용.
# templates = Jinja2Templates(directory="templates")
# @app.get("/", response_class=HTMLResponse)
# def index(request: Request):
#     return templates.TemplateResponse("index.html", {"request": request})
     

# 라우터(요청에 응답하는)
@app.post('/api/register')
def register_user(user: RegisterRequest, db:Session=Depends(get_db)):
    # 같은 사용자가 있는지 조회
    existing_user =  db.query(User) \
        .filter(User.username == user.username or User.email == user.email) \
        .first()
    # 같은 사용자가 있으면  400에러로 응답
    if existing_user:
        raise HTTPException(status_code=400, detail="이미 존재하는 사용자입니다.")
    # 새 유저에대한 객체(인스턴스) 생성성
    new_user =  User(
        username = user.username,
        email = user.email,
        password = user.password
    )
    # db commit하는 과정과 동일
    db.add(new_user)
    db.commit()
    db.refresh(new_user)  # DB에서 자동 생성된 id를 유저인스턴스에 할당
    return {"success":True,'message':'회원가입 성공', 'user_id':new_user.id}

# 사용자정보 UserCreate 로 DB 조회회
@app.post('/api/login')
def login(user:UserCreate, db:Session=Depends(get_db)):    
    found = db.query(User) \
        .filter(User.username == user.username, User.password == user.password) \
        .first()
    
    if not found:
        raise HTTPException(status_code=400, detail="로그인 실패")
    return {"success":True, 'message':'로그인 성공', 'user_id': found.id}

# 사용자의 고유 id로 user테이블의 데이터 조회
@app.get('/api/users/{user_id}',response_model=UserResponse)
def get_user(user_id:int, db:Session=Depends(get_db) ):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail='사용자를 찾을수 없습니다.')
    return user

from typing import List
# 전체상품 조회
@app.get('/api/products', response_model=List[ProductOut])
def get_produc():
    db = SessionLocal()
    products = db.query(Product).all()
    db.close()
    return products
# 상품 등록
@app.post('/api/products')
def create_produc(product: ProductCreate):
    db = SessionLocal()
    product = Product(name= product.name, price = product.price)
    db.add(product)
    db.commit()    
    db.refresh(product)
    db.close()
    return {"success":True, "message":"상품 등록 완료",'product_id':product.id}    
# 장바구니 담기
@app.post('/api/cart')
def add_to_cart(item: CartItem):
    db = SessionLocal()
    cart = Cart(user_id=item.user_id, product_id=item.product_id, quantity=item.quantity)
    db.add(cart)
    db.commit()
    db.refresh(cart)
    db.close()
    return {"success":True, "message":"장바구니에 담겼습니다.",'cart_id':cart.id}    

# 장바구니 조회  /api/cart?user_id=1   ?키=벨류&키=벨류  쿼리파라메터터
from fastapi import Query
@app.get('/api/cart')
def get_cart(user_id: int = Query(...), db:Session=Depends(get_db)):
    items = db.query(Cart).filter(Cart.user_id == user_id).all()
    return [     
        {            
            'product_id':item.product_id ,
            'quantity':item.quantity,
            'id' : item.id,

        }
     for item in items
    ]
# 주문 요청(장바구니 상품 주문)
@app.post('/api/order')
def place_order(order: OrderRequest, db:Session=Depends(get_db)):
    cart_items = db.query(Cart).filter(Cart.user_id == order.user_id).all()
    if not cart_items:
        raise HTTPException(status_code=400,detail="장바구니가 비어있습니다.")
    
    for item in cart_items:
        new_order = Order(
            user_id=item.user_id,
            product_id = item.product_id,
            quantity = item.quantity
        )
        db.add(new_order)  # 주문테이블에 추가
        db.delete(item)  # cart 테이블에서 삭제        
    db.commit()
    return {"success":True, 'message':'주문이 완료 되었습니다'}
#주문 목록 조회
@app.get('/api/order', response_model=List[OrderOut])
def get_orders(user_id:int = Query(...),db:Session=Depends(get_db)):
    orders = db.query(Order).filter(Order.user_id == user_id).all()
    # 각 주문에 상품 정보 추가
    for order in orders:
        order.product = db.query(Product).filter(Product.id == order.product_id).first()
    return orders

# 상품 상세 조회
@app.get('/api/products/{product_id}', response_model=ProductOut)
def get_product_detail(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")
    return product

# 상품 수정
@app.put('/api/products/{product_id}')
def update_product(product_id: int, product: ProductCreate, db: Session = Depends(get_db)):
    existing_product = db.query(Product).filter(Product.id == product_id).first()
    if not existing_product:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")
    
    existing_product.name = product.name
    existing_product.price = product.price
    db.commit()
    db.refresh(existing_product)
    return {"success": True, "message": "상품이 수정되었습니다.", "product_id": existing_product.id}

# 상품 삭제
@app.delete('/api/products/{product_id}')
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")
    
    db.delete(product)
    db.commit()
    return {"success": True, "message": "상품이 삭제되었습니다."}

# 장바구니 상품 수량 수정
@app.put('/api/cart/{cart_id}')
def update_cart_item(cart_id: int, quantity: int = Query(..., gt=0), db: Session = Depends(get_db)):
    cart_item = db.query(Cart).filter(Cart.id == cart_id).first()
    if not cart_item:
        raise HTTPException(status_code=404, detail="장바구니 상품을 찾을 수 없습니다.")
    
    cart_item.quantity = quantity
    db.commit()
    db.refresh(cart_item)
    return {"success": True, "message": "장바구니 상품 수량이 수정되었습니다.", "cart_id": cart_item.id}

# 장바구니 상품 삭제
@app.delete('/api/cart/{cart_id}')
def delete_cart_item(cart_id: int, db: Session = Depends(get_db)):
    cart_item = db.query(Cart).filter(Cart.id == cart_id).first()
    if not cart_item:
        raise HTTPException(status_code=404, detail="장바구니 상품을 찾을 수 없습니다.")
    
    db.delete(cart_item)
    db.commit()
    return {"success": True, "message": "장바구니 상품이 삭제되었습니다."}

# 정적 HTML 파일 서빙
# FAST api 방식
# app.mount("/", StaticFiles(directory="templates", html=True), name="static")

# 주문 상세 조회
@app.get('/api/orders/{order_id}', response_model=OrderOut)
def get_order_detail(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="주문을 찾을 수 없습니다.")
    return order

# 주문 상태 변경
@app.put('/api/orders/{order_id}/status')
def update_order_status(order_id: int, status: str = Query(..., regex="^(pending|processing|completed|cancelled)$"), db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="주문을 찾을 수 없습니다.")
    
    order.status = status
    db.commit()
    db.refresh(order)
    return {"success": True, "message": "주문 상태가 변경되었습니다.", "order_id": order.id}

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting API server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)