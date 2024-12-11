import os
import secrets
from dotenv import load_dotenv
from flask import Flask, render_template, request, send_from_directory, jsonify, Response, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from email_validator import validate_email, EmailNotValidError
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from werkzeug.utils import secure_filename
from sklearn.datasets import load_iris, fetch_california_housing, load_diabetes
import time
import json
import io
import base64

# 加载环境变量
load_dotenv()

# 创建 Flask 应用
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(16))
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'sqlite:///dssec.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['RESULT_FOLDER'] = os.path.join(os.path.dirname(__file__), 'results')

# 初始化数据库和登录管理
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# 用户模型
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# 用户加载器
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 创建数据库表
with app.app_context():
    db.create_all()

# 注册路由
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # 服务器端验证
        if not username or not email or not password:
            return jsonify({'success': False, 'message': '请填写所有必填字段'})

        # 验证邮箱
        try:
            valid = validate_email(email)
            email = valid.email
        except EmailNotValidError as e:
            return jsonify({'success': False, 'message': str(e)})

        # 检查用户是否已存在
        if User.query.filter_by(username=username).first():
            return jsonify({'success': False, 'message': '用户名已存在'})
        
        if User.query.filter_by(email=email).first():
            return jsonify({'success': False, 'message': '邮箱已被注册'})

        # 创建新用户
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            return jsonify({'success': True, 'message': '注册成功，请登录', 'redirect': url_for('login')})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': f'注册失败：{str(e)}'})

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # 服务器端验证
        if not username or not password:
            return jsonify({'success': False, 'message': '请输入用户名和密码'})
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return jsonify({'success': True, 'redirect': url_for('index')})
        else:
            return jsonify({'success': False, 'message': '用户名或密码错误'})
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# 其他原有的路由和函数保持不变
# ... (保留原有的 analyze_data, upload_file 等函数)

@app.route('/')
@login_required
def index():
    return render_template('index.html', username=current_user.username)

@app.route('/about')
def about():
    return render_template('about.html')

# 生成分析进度
def generate_progress(total_steps=5):
    """生成分析进度"""
    try:
        steps = [
            '初始化数据处理',
            '检查数据类型',
            '准备统计分析',
            '生成可视化图表',
            '完成数据分析'
        ]
        
        for i in range(total_steps):
            progress = int((i + 1) / total_steps * 100)
            print(f"Sending progress: {progress}%")  # 添加调试日志
            yield f"data: {json.dumps({'progress': progress, 'message': steps[i]})}\n\n"
            time.sleep(1)  # 增加等待时间
        
        # 确保最后一次发送100%进度
        print("Sending final progress: 100%")  # 添加调试日志
        yield f"data: {json.dumps({'progress': 100, 'message': '分析完成'})}\n\n"
    except Exception as e:
        print(f"Progress generation error: {e}")  # 捕获并打印异常

def load_sample_dataset(dataset_name):
    """加载示例数据集并转换为DataFrame"""
    try:
        if dataset_name == 'iris':
            data = load_iris()
            df = pd.DataFrame(data.data, columns=data.feature_names)
            df['target'] = data.target
            df['target_names'] = df['target'].map(dict(enumerate(data.target_names)))
        elif dataset_name == 'california_housing':
            data = fetch_california_housing()
            df = pd.DataFrame(data.data, columns=data.feature_names)
            df['target'] = data.target
        elif dataset_name == 'diabetes':
            data = load_diabetes()
            df = pd.DataFrame(data.data, columns=data.feature_names)
            df['disease_progression'] = data.target
        else:
            return {'error': '未知数据集'}
        
        return df
    except Exception as e:
        return {'error': str(e)}

def analyze_data(df, max_rows=10000):
    try:
        # 随机采样大型数据集
        if len(df) > max_rows:
            df = df.sample(n=max_rows, random_state=42)
        
        # 选择数值列
        numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # 检查是否有数值列
        if len(numeric_columns) == 0:
            return {'error': '未找到数值列，请确保数据集包含数值类型的列'}
        
        # 生成图表
        def generate_charts(df, numeric_columns):
            try:
                charts = []
                
                # 1. 相关性热力图
                plt.figure(figsize=(10, 8))
                correlation_matrix = df[numeric_columns].corr()
                sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', 
                            square=True, linewidths=0.5, cbar_kws={"shrink": .8})
                plt.title('数据特征相关性热力图')
                buffer = io.BytesIO()
                plt.savefig(buffer, format='png', dpi=300)
                buffer.seek(0)
                charts.append(base64.b64encode(buffer.getvalue()).decode('utf-8'))
                plt.close()

                # 2. 箱线图
                plt.figure(figsize=(12, 6))
                df[numeric_columns].boxplot()
                plt.title('数值特征箱线图')
                plt.xticks(rotation=45)
                buffer = io.BytesIO()
                plt.savefig(buffer, format='png', dpi=300)
                buffer.seek(0)
                charts.append(base64.b64encode(buffer.getvalue()).decode('utf-8'))
                plt.close()

                # 3. 直方图
                plt.figure(figsize=(12, 6))
                df[numeric_columns].hist(bins=10)
                plt.suptitle('数值特征直方图')
                buffer = io.BytesIO()
                plt.savefig(buffer, format='png', dpi=300)
                buffer.seek(0)
                charts.append(base64.b64encode(buffer.getvalue()).decode('utf-8'))
                plt.close()

                return charts
            except Exception as e:
                print(f"图表生成错误: {e}")
                return []
        
        # 同步生成图表
        chart_base64_list = generate_charts(df, numeric_columns)
        
        # 快速计算统计信息
        stats_data = {}
        for col in numeric_columns:
            try:
                stats_data[col] = {
                    'mean': round(df[col].mean(), 2),
                    'median': round(df[col].median(), 2),
                    'std': round(df[col].std(), 2),
                    'min': round(df[col].min(), 2),
                    'max': round(df[col].max(), 2)
                }
            except Exception as e:
                stats_data[col] = {'error': f'统计计算失败：{str(e)}'}
        
        return {
            'stats': stats_data,
            'chart_base64_list': chart_base64_list
        }
    except Exception as e:
        return {'error': f'数据分析发生错误：{str(e)}'}

@app.route('/progress')
def progress():
    """服务器推送进度信息"""
    def generate_progress_stream():
        try:
            steps = [
                '初始化数据处理',
                '检查数据类型',
                '准备统计分析',
                '生成可视化图表',
                '完成数据分析'
            ]
            
            for i in range(5):  # 总共5个步骤
                progress = int((i + 1) / 5 * 100)
                print(f"Progress: {progress}% - {steps[i]}")  # 服务器端日志
                
                # 使用 SSE 格式发送数据
                yield f"data: {json.dumps({'progress': progress, 'message': steps[i]})}\n\n"
                time.sleep(1)  # 每步骤间隔1秒
            
            # 发送最终100%进度
            yield f"data: {json.dumps({'progress': 100, 'message': '分析完成'})}\n\n"
        
        except GeneratorExit:
            print("Progress stream closed")
        except Exception as e:
            print(f"Progress generation error: {e}")
            yield f"data: {json.dumps({'progress': 0, 'message': f'错误：{str(e)}', 'error': True})}\n\n"

    return Response(generate_progress_stream(), mimetype='text/event-stream')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        # 检查是否有文件上传
        if 'file' not in request.files:
            return jsonify({'error': '没有文件上传'}), 400
        
        file = request.files['file']
        
        # 检查文件名
        if file.filename == '':
            return jsonify({'error': '未选择文件'}), 400
        
        # 检查文件类型
        if not file.filename.lower().endswith('.csv'):
            return jsonify({'error': '仅支持CSV文件'}), 400
        
        # 安全保存文件名
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        try:
            # 保存文件
            file.save(filepath)
        except Exception as save_error:
            return jsonify({'error': f'文件保存失败：{str(save_error)}'}), 500
        
        # 读取CSV文件，支持多种编码
        try:
            # 尝试UTF-8编码
            df = pd.read_csv(filepath, encoding='utf-8')
        except UnicodeDecodeError:
            # 尝试GBK编码
            try:
                df = pd.read_csv(filepath, encoding='gbk')
            except Exception as encoding_error:
                return jsonify({'error': f'文件编码错误：{str(encoding_error)}'}), 400
        except pd.errors.EmptyDataError:
            return jsonify({'error': '文件为空'}), 400
        except pd.errors.ParserError as parse_error:
            return jsonify({'error': f'文件解析错误：{str(parse_error)}'}), 400
        except Exception as read_error:
            return jsonify({'error': f'文件读取失败：{str(read_error)}'}), 500
        
        # 分析数据
        try:
            result = analyze_data(df)
            
            # 检查分析结果是否有错误
            if 'error' in result:
                return jsonify(result), 400
            
            return jsonify(result)
        
        except Exception as analyze_error:
            return jsonify({'error': f'数据分析失败：{str(analyze_error)}'}), 500
    
    except Exception as e:
        return jsonify({'error': f'上传处理发生未知错误：{str(e)}'}), 500

@app.route('/sample_dataset/<dataset_name>')
def sample_dataset(dataset_name):
    """处理示例数据集的路由"""
    df = load_sample_dataset(dataset_name)
    
    if isinstance(df, dict) and 'error' in df:
        return jsonify(df)
    
    result = analyze_data(df)
    return jsonify(result)

@app.route('/results/<filename>')
def serve_result(filename):
    """提供分析结果图片"""
    try:
        # 确保只能访问 results 目录下的图片
        return send_from_directory(app.config['RESULT_FOLDER'], filename)
    except Exception as e:
        print(f"图片服务错误: {e}")
        return jsonify({'error': '图片加载失败'}), 404

@app.route('/serve_image', methods=['POST'])
def serve_image():
    """动态获取图片路径"""
    try:
        filename = request.json.get('filename')
        if not filename:
            return jsonify({'error': '未指定图片文件名'}), 400
        
        filepath = os.path.join(app.config['RESULT_FOLDER'], filename)
        
        if not os.path.exists(filepath):
            return jsonify({'error': '图片不存在'}), 404
        
        return jsonify({
            'url': f'/results/{filename}',
            'exists': True
        })
    except Exception as e:
        print(f"图片路径获取错误: {e}")
        return jsonify({'error': '图片路径获取失败'}), 500

def generate_charts(df):
    """
    生成多种类型的图表
    :param df: 输入的 DataFrame
    :return: 图表的 base64 编码列表
    """
    try:
        charts = []
        # 选择数值列
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
        
        if not numeric_cols:
            raise ValueError("没有可用于绘图的数值列")

        plt.figure(figsize=(12, 8))
        plt.clf()  # 清除当前图形

        # 1. 柱状图：列平均值
        plt.subplot(2, 3, 1)
        df[numeric_cols].mean().plot(kind='bar')
        plt.title('列平均值')
        plt.xticks(rotation=45, ha='right')

        # 2. 折线图：数值列趋势
        plt.subplot(2, 3, 2)
        df[numeric_cols].plot(kind='line')
        plt.title('数值列趋势')
        plt.legend(loc='best')

        # 3. 箱线图：数值列分布
        plt.subplot(2, 3, 3)
        df[numeric_cols].boxplot()
        plt.title('数值列分布')
        plt.xticks(rotation=45, ha='right')

        # 4. 热力图：相关性
        plt.subplot(2, 3, 4)
        sns.heatmap(df[numeric_cols].corr(), annot=True, cmap='coolwarm', center=0)
        plt.title('相关性热力图')

        # 5. 直方图：数值列分布
        plt.subplot(2, 3, 5)
        df[numeric_cols].hist(bins=10)
        plt.suptitle('数值列直方图')

        plt.tight_layout()
        
        # 保存为 base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=300)
        buffer.seek(0)
        chart_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        charts.append(chart_base64)
        plt.close()

        return charts

    except Exception as e:
        app.logger.error(f"图表生成错误: {str(e)}")
        return []

@app.route('/visualize', methods=['GET', 'POST'])
@login_required
def visualize():
    if request.method == 'POST':
        # 处理文件上传
        if 'file' not in request.files:
            return jsonify({
                'error': '没有选择文件',
                'status': 'error'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'error': '没有选择文件',
                'status': 'error'
            }), 400
        
        if file and file.filename.endswith('.csv'):
            try:
                # 读取 CSV 文件
                df = pd.read_csv(file)
                
                # 选择数值列
                numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
                
                # 检查是否有数值列
                if len(numeric_columns) == 0:
                    return jsonify({
                        'error': '未找到数值列，请确保数据集包含数值类型的列',
                        'status': 'error'
                    }), 400
                
                # 生成图表
                chart_base64_list = generate_charts(df)
                
                return jsonify({
                    'chart_base64_list': chart_base64_list,
                    'status': 'success'
                }), 200
            
            except Exception as e:
                app.logger.error(f"文件处理错误: {str(e)}")
                return jsonify({
                    'error': f'文件处理错误：{str(e)}',
                    'status': 'error'
                }), 500
        
        return jsonify({
            'error': '请上传 CSV 文件',
            'status': 'error'
        }), 400
    
    return render_template('visualize.html')

if __name__ == '__main__':
    app.run(debug=True)
