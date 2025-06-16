from flask import Flask, render_template
from flask import redirect, url_for, session, flash, request
import requests
app = Flask(__name__)

app.secret_key = 'your_secret_key'  # 세션을 사용하기 위한 비밀키 설정

# 로그인 체크 데코레이터
def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('로그인이 필요합니다.', 'danger')
            return redirect(url_for('login', next=request.url))  # 로그인 페이지로 리다이렉트
        return f(*args, **kwargs)   # 원래 실행하려던 라우트 함수를 실행
    decorated_function.__name__ = f.__name__  # 데코레이터로 인해 함수 이름이 변경되므로 원래 이름으로 복원
    return decorated_function

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('로그아웃 되었습니다.', 'success')
    return redirect(url_for('home'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        response =  requests.post('http://localhost:8000/api/login', 
            json={
                'username': username,
                'password': password
            })
        if response.status_code == 200:
            session['user_id'] = response.json().get('user_id')
            session['username'] = username
            flash('로그인 성공!', 'success')
            return redirect(url_for('home'))
        else:
            return render_template('register.html', error='로그인 실패')
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/products')
@login_required
def products():
    return render_template('products.html')

@app.route('/cart')
@login_required
def cart():
    return render_template('cart.html')

@app.route('/orders')
@login_required
def orders():
    return render_template('orders.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)