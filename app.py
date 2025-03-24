# app.py
from flask import Flask, jsonify, request
from flask_cors import CORS
from controllers.exam_resources import exam_bp
from config import API_CONFIG
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 配置CORS以支持微信小程序请求
CORS(app, resources={r"/*": {
    "origins": "*",
    "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "supports_credentials": True,
    "max_age": 86400
}})

# 注册蓝图
app.register_blueprint(exam_bp)

@app.route("/api/health", methods=["GET"])
def health_check():
    """健康检查接口"""
    return jsonify({
        "status": "ok",
        "message": "Service is running"
    })

@app.after_request
def after_request(response):
    """请求处理后的钩子，添加必要的响应头"""
    if request.method == 'OPTIONS':
        response.status_code = 200
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('Access-Control-Max-Age', '86400')
    return response

if __name__ == "__main__":
    logger.info(f"Starting API server on port {API_CONFIG['port']}")
    app.run(
        host="0.0.0.0", 
        port=API_CONFIG["port"],
        debug=API_CONFIG["debug"],
        threaded=True
    )
