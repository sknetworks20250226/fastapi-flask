from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import requests
import json
from functools import wraps
import logging
import sys
from logging.handlers import TimedRotatingFileHandler
import os
from datetime import datetime

# 현재 스크립트의 절대 경로
current_dir = os.path.dirname(os.path.abspath(__file__))
# 프로젝트 루트 디렉토리 (frontend의 상위 디렉토리)
project_root = os.path.dirname(current_dir)
# 로그 디렉토리 경로
log_dir = os.path.join(project_root, 'logs')

# 로그 디렉토리 생성
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
    print(f'Created log directory at: {log_dir}')

# 로그 파일 경로 설정
log_file = os.path.join(log_dir, 'app.log')
print(f'Log file will be saved at: {log_file}')

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
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
logger.info(f'Logging initialized. Log directory: {log_dir}')

# Flask 애플리케이션 설정
app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # 실제 운영 환경에서는 안전한 키로 변경해야 합니다
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 세션 유효 시간을 1시간으로 설정

# Flask 로거 설정
app.logger.setLevel(logging.DEBUG)
# Flask의 기본 로거 핸들러 제거
for handler in app.logger.handlers[:]:
    app.logger.removeHandler(handler)
# 우리가 만든 로거 핸들러 추가
app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.addHandler(TimedRotatingFileHandler(
    filename=log_file,
    when='midnight',
    interval=1,
    backupCount=30,
    encoding='utf-8'
))

# 세션 설정을 위한 before_request 핸들러
@app.before_request
def before_request():
    session.permanent = True  # 모든 요청에서 세션을 영구적으로 설정
    app.logger.debug(f'Request path: {request.path}')
    app.logger.debug(f'Request method: {request.method}')
    app.logger.debug(f'Current session: {dict(session)}')

# 로그인 체크 데코레이터
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            app.logger.debug(f'Protected URL: {request.url}')
            app.logger.debug(f'Request path: {request.path}')
            app.logger.debug(f'Request full path: {request.full_path}')
            return redirect(url_for('login', next=request.path))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    app.logger.debug('Accessing index page')
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    app.logger.debug(f'Login request method: {request.method}')
    app.logger.debug(f'Login next parameter: {request.args.get("next")}')
    app.logger.debug(f'Current session: {dict(session)}')
    
    if request.method == 'POST':
        try:
            app.logger.debug(f'Login request data: {request.get_json()}')
            response = requests.post('http://localhost:8000/api/login',             
                                   json=request.get_json())
            app.logger.debug(f'Login API response status: {response.status_code}')
            app.logger.debug(f'Login API response data: {response.json()}')
            
            if response.status_code == 200:
                data = response.json()
                session['user_id'] = data['user_id']
                session['username'] = request.get_json()['username']
                session.permanent = True  # 세션을 영구적으로 설정
                
                app.logger.info(f'Login successful for user: {session["username"]}')
                app.logger.debug(f'Updated session: {dict(session)}')
                
                return jsonify({
                    "success": True,
                    "redirect": url_for('index')
                })
            else:
                app.logger.warning(f'Login failed with status: {response.status_code}')
                return jsonify({"success": False, "message": "로그인에 실패했습니다."}), 400
        except Exception as e:
            app.logger.error(f'Login error: {str(e)}', exc_info=True)
            return jsonify({"success": False, "message": "서버 오류가 발생했습니다."}), 500
    
    return render_template('login.html', next=request.args.get('next', ''))

@app.route('/logout')
def logout():
    username = session.get('username', 'unknown')
    app.logger.info(f'User logged out: {username}')
    session.clear()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        app.logger.debug(f'Registration attempt for user: {username}')
        
        try:
            response = requests.post('http://localhost:8000/api/register', 
                                   json={'username': username, 'email': email, 'password': password})
            
            if response.status_code == 200:
                app.logger.info(f'Registration successful for user: {username}')
                return redirect(url_for('login'))
            else:
                app.logger.warning(f'Registration failed for user: {username}')
                return render_template('register.html', error='회원가입에 실패했습니다.')
        except Exception as e:
            app.logger.error(f'Registration error: {str(e)}', exc_info=True)
            return render_template('register.html', error='서버 오류가 발생했습니다.')
    
    return render_template('register.html')

@app.route('/products')
@login_required
def products():
    app.logger.debug('Accessing products page')
    return render_template('products.html')

@app.route('/cart')
@login_required
def cart():
    app.logger.debug('Accessing cart page')
    return render_template('cart.html')

@app.route('/orders')
@login_required
def orders():
    app.logger.debug('Accessing orders page')
    return render_template('orders.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)