
from flask import Blueprint, request, jsonify
from utils.db import db
from utils.cos_client import cos_client
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

exam_bp = Blueprint("exam", __name__)

@exam_bp.route("/api/exam/resources", methods=["GET"])
def get_exam_resources():
    """获取考试资源列表"""
    try:
        # 获取查询参数
        exam_type = request.args.get("exam_type", "cet")
        category = request.args.get("category")
        year = request.args.get("year")
        
        # 构建SQL查询
        sql = "SELECT * FROM exam_resources WHERE exam_type = %s"
        params = [exam_type]
        
        if category:
            sql += " AND category = %s"
            params.append(category)
        
        if year:
            sql += " AND year = %s"
            params.append(int(year))
            
        sql += " ORDER BY year DESC, title ASC"
        
        # 执行查询
        resources = db.execute_query(sql, params)
        
        # 对结果进行处理，包括检查用户是否收藏过
        user_id = request.args.get("user_id", "")
        if user_id:
            # 获取该用户的收藏列表
            favorites_sql = "SELECT resource_id FROM user_favorites WHERE user_id = %s"
            favorites = db.execute_query(favorites_sql, [user_id])
            favorite_ids = [fav["resource_id"] for fav in favorites]
            
            # 为每个资源添加收藏标记
            for resource in resources:
                resource["is_favorite"] = resource["id"] in favorite_ids
        
        logger.info(f"Retrieved {len(resources)} resources for exam_type={exam_type}")
        return jsonify({
            "code": 0,
            "message": "success",
            "data": resources
        })
    except Exception as e:
        logger.error(f"Error fetching resources: {str(e)}")
        return jsonify({
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }), 500

@exam_bp.route("/api/exam/download", methods=["POST"])
def get_download_url():
    """获取文件下载链接"""
    try:
        data = request.json
        resource_id = data.get("resource_id")
        user_id = data.get("user_id", "anonymous")
        
        # 验证参数
        if not resource_id:
            return jsonify({
                "code": 400,
                "message": "Missing resource_id",
                "data": None
            }), 400
            
        # 获取资源信息
        resource = db.execute_query("SELECT * FROM exam_resources WHERE id = %s", [resource_id])
        if not resource:
            return jsonify({
                "code": 404,
                "message": "Resource not found",
                "data": None
            }), 404
            
        resource = resource[0]
        
        # 获取临时下载链接
        download_url = cos_client.get_presigned_url(resource["file_id"], expires=3600)
        
        # 记录下载
        if user_id != "anonymous":
            db.execute_insert(
                "INSERT INTO user_downloads (user_id, resource_id, ip_address) VALUES (%s, %s, %s)",
                [user_id, resource_id, request.remote_addr]
            )
        
        # 更新下载次数
        db.execute_update(
            "UPDATE exam_resources SET download_count = download_count + 1 WHERE id = %s",
            [resource_id]
        )
        
        logger.info(f"Generated download URL for resource_id={resource_id}, user_id={user_id}")
        return jsonify({
            "code": 0,
            "message": "success",
            "data": {
                "download_url": download_url,
                "file_name": resource["title"],
                "file_type": resource["file_type"]
            }
        })
    except Exception as e:
        logger.error(f"Error generating download URL: {str(e)}")
        return jsonify({
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }), 500

@exam_bp.route("/api/exam/favorite", methods=["POST"])
def toggle_favorite():
    """添加或删除收藏"""
    try:
        data = request.json
        resource_id = data.get("resource_id")
        user_id = data.get("user_id")
        action = data.get("action", "add")  # "add" 或 "remove"
        
        # 验证参数
        if not resource_id or not user_id:
            return jsonify({
                "code": 400,
                "message": "Missing required parameters",
                "data": None
            }), 400
            
        if action == "add":
            # 添加收藏
            try:
                db.execute_insert(
                    "INSERT INTO user_favorites (user_id, resource_id) VALUES (%s, %s)",
                    [user_id, resource_id]
                )
                
                # 更新收藏次数
                db.execute_update(
                    "UPDATE exam_resources SET favorite_count = favorite_count + 1 WHERE id = %s",
                    [resource_id]
                )
                
                message = "Favorite added"
            except Exception as ex:
                if "Duplicate entry" in str(ex):
                    # 已经收藏了，不需要操作
                    message = "Already favorited"
                else:
                    raise ex
        else:
            # 移除收藏
            affected_rows = db.execute_update(
                "DELETE FROM user_favorites WHERE user_id = %s AND resource_id = %s",
                [user_id, resource_id]
            )
            
            if affected_rows > 0:
                # 更新收藏次数
                db.execute_update(
                    "UPDATE exam_resources SET favorite_count = GREATEST(0, favorite_count - 1) WHERE id = %s",
                    [resource_id]
                )
                message = "Favorite removed"
            else:
                message = "Not favorited"
        
        logger.info(f"Toggle favorite: action={action}, resource_id={resource_id}, user_id={user_id}")
        return jsonify({
            "code": 0,
            "message": message,
            "data": {"action": action}
        })
    except Exception as e:
        logger.error(f"Error toggling favorite: {str(e)}")
        return jsonify({
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }), 500

@exam_bp.route("/api/exam/favorites", methods=["GET"])
def get_user_favorites():
    """获取用户收藏列表"""
    try:
        user_id = request.args.get("user_id")
        
        if not user_id:
            return jsonify({
                "code": 400,
                "message": "Missing user_id",
                "data": None
            }), 400
            
        # 获取用户收藏的资源
        sql = """
        SELECT r.*, f.create_time as favorite_time 
        FROM exam_resources r
        JOIN user_favorites f ON r.id = f.resource_id
        WHERE f.user_id = %s
        ORDER BY f.create_time DESC
        """
        
        favorites = db.execute_query(sql, [user_id])
        
        logger.info(f"Retrieved {len(favorites)} favorites for user_id={user_id}")
        return jsonify({
            "code": 0,
            "message": "success",
            "data": favorites
        })
    except Exception as e:
        logger.error(f"Error fetching favorites: {str(e)}")
        return jsonify({
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }), 500

@exam_bp.route("/api/exam/downloads", methods=["GET"])
def get_user_downloads():
    """获取用户下载历史"""
    try:
        user_id = request.args.get("user_id")
        
        if not user_id:
            return jsonify({
                "code": 400,
                "message": "Missing user_id",
                "data": None
            }), 400
            
        # 获取用户下载的资源
        sql = """
        SELECT r.*, d.download_time 
        FROM exam_resources r
        JOIN user_downloads d ON r.id = d.resource_id
        WHERE d.user_id = %s
        ORDER BY d.download_time DESC
        """
        
        downloads = db.execute_query(sql, [user_id])
        
        logger.info(f"Retrieved {len(downloads)} download history for user_id={user_id}")
        return jsonify({
            "code": 0,
            "message": "success",
            "data": downloads
        })
    except Exception as e:
        logger.error(f"Error fetching download history: {str(e)}")
        return jsonify({
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }), 500

@exam_bp.route("/api/exam/favorite", methods=["POST"])
def toggle_favorite():
    """添加或删除收藏"""
    try:
        data = request.json
        resource_id = data.get("resource_id")
        user_id = data.get("user_id")
        action = data.get("action", "add")  # "add" 或 "remove"
        
        # 验证参数
        if not resource_id or not user_id:
            return jsonify({
                "code": 400,
                "message": "Missing required parameters",
                "data": None
            }), 400
            
        if action == "add":
            # 添加收藏
            try:
                db.execute_insert(
                    "INSERT INTO user_favorites (user_id, resource_id) VALUES (%s, %s)",
                    [user_id, resource_id]
                )
                
                # 更新收藏次数
                db.execute_update(
                    "UPDATE exam_resources SET favorite_count = favorite_count + 1 WHERE id = %s",
                    [resource_id]
                )
                
                message = "Favorite added"
            except Exception as ex:
                if "Duplicate entry" in str(ex):
                    # 已经收藏了，不需要操作
                    message = "Already favorited"
                else:
                    raise ex
        else:
            # 移除收藏
            affected_rows = db.execute_update(
                "DELETE FROM user_favorites WHERE user_id = %s AND resource_id = %s",
                [user_id, resource_id]
            )
            
            if affected_rows > 0:
                # 更新收藏次数
                db.execute_update(
                    "UPDATE exam_resources SET favorite_count = GREATEST(0, favorite_count - 1) WHERE id = %s",
                    [resource_id]
                )
                message = "Favorite removed"
            else:
                message = "Not favorited"
        
        logger.info(f"Toggle favorite: action={action}, resource_id={resource_id}, user_id={user_id}")
        return jsonify({
            "code": 0,
            "message": message,
            "data": {"action": action}
        })
    except Exception as e:
        logger.error(f"Error toggling favorite: {str(e)}")
        return jsonify({
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }), 500

@exam_bp.route("/api/exam/favorites", methods=["GET"])
def get_user_favorites():
    """获取用户收藏列表"""
    try:
        user_id = request.args.get("user_id")
        
        if not user_id:
            return jsonify({
                "code": 400,
                "message": "Missing user_id",
                "data": None
            }), 400
            
        # 获取用户收藏的资源
        sql = """
        SELECT r.*, f.create_time as favorite_time 
        FROM exam_resources r
        JOIN user_favorites f ON r.id = f.resource_id
        WHERE f.user_id = %s
        ORDER BY f.create_time DESC
        """
        
        favorites = db.execute_query(sql, [user_id])
        
        logger.info(f"Retrieved {len(favorites)} favorites for user_id={user_id}")
        return jsonify({
            "code": 0,
            "message": "success",
            "data": favorites
        })
    except Exception as e:
        logger.error(f"Error fetching favorites: {str(e)}")
        return jsonify({
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }), 500

@exam_bp.route("/api/exam/downloads", methods=["GET"])
def get_user_downloads():
    """获取用户下载历史"""
    try:
        user_id = request.args.get("user_id")
        
        if not user_id:
            return jsonify({
                "code": 400,
                "message": "Missing user_id",
                "data": None
            }), 400
            
        # 获取用户下载的资源
        sql = """
        SELECT r.*, d.download_time 
        FROM exam_resources r
        JOIN user_downloads d ON r.id = d.resource_id
        WHERE d.user_id = %s
        ORDER BY d.download_time DESC
        """
        
        downloads = db.execute_query(sql, [user_id])
        
        logger.info(f"Retrieved {len(downloads)} download history for user_id={user_id}")
        return jsonify({
            "code": 0,
            "message": "success",
            "data": downloads
        })
    except Exception as e:
        logger.error(f"Error fetching download history: {str(e)}")
        return jsonify({
            "code": 500,
            "message": f"Error: {str(e)}",
            "data": None
        }), 500
