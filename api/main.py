# FAST API의 메인 서버
from fastapi import FastAPI,HTTPException,Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from model import *
from database import SessionLocal,engin
from schemas import *
from fastapi.staticfiles import StaticFiles
# Fast api 생성
app = FastAPI()

# 앱을 실행하면 DB에 정의된 모든 테이블을 생성
Base.metadata.create_all(bind=engin)

def get_db():
    db = SessionLocal()  # 새션 객체  생성
    try:
        yield db # 종속된 함수에 세션 주입
    finally:
        db.close()  # 요청이 끝나면 자동으로 세션 종료
# 회원가입용 데이터타입  pydantic 
class RegisterRequest(BaseModel):
    username: str
    email: str
    passowrd: str

from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import FastAPI, Request

# 템플릿 디렉토리 설정
# pip install jinja2
templates = Jinja2Templates(directory="templates")
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
     

# 라우터(요청에 응답하는)
@app.post('/api/register')
def register_user(user: RegisterRequest, db:Session=Depends(get_db)):
    # 같은 사용자가 있는지 조회
    existing_user =  db.query(User).filter(User.username == user.username).first()
    # 같은 사용자가 있으면  400에러로 응답
    if existing_user:
        raise HTTPException(status_code=400, detail="이미 존재하는 사용자입니다.")
    # 새 유저에대한 객체(인스턴스) 생성성
    new_user =  User(
        username = user.username,
        email = user.email,
        password = user.passowrd
    )
    # db commit하는 과정과 동일
    db.add(new_user)
    db.commit()
    db.refresh(new_user)  # DB에서 자동 생성된 id를 유저인스턴스에 할당
    return {"success":True,'message':'회원가입 성공', 'user_id':new_user.id}

# 사용자정보 UserCreate 로 DB 조회회
@app.post('/api/login')
def login(user:UserCreate, db:Session=Depends(get_db)):
    # 사용자 테이블에서 입력한 이름과 패스워드가 있는지 조회
    print(user)
    found =  db.query(User) \
        .filter(User.username == user.username, User.password == user.password) \
        .first()
    
    if not found:
        raise HTTPException(status_code=400, detail="로그인 실패")
    return {"success":True,'message':'로그인 성공'}

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
            'quantity':item.quantity
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
        db.refresh(new_order)  # DB에서 새로 생성된 primary key 값을 new_order 의 id에 저장
    db.commit()
    return {"success":True, 'message':'주문이 완료 되었습니다'}
#주문 목록 조회
@app.get('/api/order', response_model=List[OrderOut])
def get_orders(user_id:int = Query(...),db:Session=Depends(get_db)):
    orders = db.query(Order).filter(Order.user_id == user_id).all()
    return orders

# 정적 HTML 파일 서빙
app.mount("/", StaticFiles(directory="templates", html=True), name="static")