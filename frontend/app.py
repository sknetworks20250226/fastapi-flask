from flask import Flask, render_template
from flask import request,redirect, url_for, session, flash
app = Flask(__name__)

app.secret_key = 'your_secret_key'  # 세션을 사용하기 위한 비밀키 설정

# 로그인 체크 데코레이터
def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('로그인이 필요합니다.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)   # 원래 실행하려던 라우트 함수를 실행
    return decorated_function

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        response =  request.post('http://localhost:8000/api/login', 
            json={
                'username': username,
                'password': password
            })
        if response.status_code == 200:
            session['user_id'] = response.json().get('user_id')
            flash('로그인 성공!', 'success')
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error='로그인 실패')
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/products')
def products():
    return render_template('products.html')

@app.route('/cart')
def cart():
    return render_template('cart.html')

@app.route('/orders')
def orders():
    return render_template('orders.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)