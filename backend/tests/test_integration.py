"""
集成测试
测试API端点和完整业务流程
"""
import pytest
import asyncio
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.models.schemas import PrescriptionType


# 测试数据库配置
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """覆盖数据库依赖"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_database():
    """确保所有集成测试都在已建表的临时数据库中运行。"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


class TestHealthCheck:
    """健康检查测试"""
    
    def test_health_check(self):
        """测试健康检查接口"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data


class TestPrescriptionAPI:
    """方剂API集成测试"""
    
    def test_create_prescription(self):
        """测试创建方剂API"""
        prescription_data = {
            "name": "四君子汤",
            "pinyin": "Si Jun Zi Tang",
            "type": "经典名方",
            "source": "《太平惠民和剂局方》",
            "functions": "益气健脾",
            "indications": "脾胃气虚证",
            "herbs": [
                {"herb_id": 1, "name": "人参", "dosage": "9g", "order": 1},
                {"herb_id": 2, "name": "白术", "dosage": "9g", "order": 2},
                {"herb_id": 3, "name": "茯苓", "dosage": "9g", "order": 3}
            ]
        }
        
        response = client.post("/api/v1/prescriptions", json=prescription_data)
        assert response.status_code == 401
        assert response.json()["code"] == "AUTHENTICATION_ERROR"
    
    def test_list_prescriptions(self):
        """测试获取方剂列表API"""
        response = client.get("/api/v1/prescriptions")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "SUCCESS"
        assert "data" in data
    
    def test_list_prescriptions_with_pagination(self):
        """测试分页获取方剂列表"""
        response = client.get("/api/v1/prescriptions?page=1&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "SUCCESS"
    
    def test_search_prescriptions(self):
        """测试搜索方剂API"""
        response = client.get("/api/v1/prescriptions/search?query=四君子")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "SUCCESS"
    
    def test_get_nonexistent_prescription(self):
        """测试获取不存在的方剂"""
        response = client.get("/api/v1/prescriptions/99999")
        assert response.status_code == 404
        data = response.json()
        assert data["code"] == "NOT_FOUND"
        assert "message" in data


class TestErrorHandling:
    """错误处理测试"""
    
    def test_invalid_json(self):
        """测试无效JSON请求"""
        response = client.post(
            "/api/v1/prescriptions",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    def test_missing_required_fields(self):
        """测试缺少必填字段"""
        invalid_data = {
            "name": "测试方"
            # 缺少herbs字段
        }
        
        response = client.post("/api/v1/prescriptions", json=invalid_data)
        assert response.status_code == 401
        assert response.json()["code"] == "AUTHENTICATION_ERROR"
    
    def test_invalid_page_number(self):
        """测试无效页码"""
        response = client.get("/api/v1/prescriptions?page=0")
        assert response.status_code == 422
    
    def test_invalid_page_size(self):
        """测试无效每页数量"""
        response = client.get("/api/v1/prescriptions?page_size=501")
        assert response.status_code == 422


class TestAPIResponseFormat:
    """API响应格式测试"""
    
    def test_response_structure(self):
        """测试响应结构"""
        response = client.get("/health")
        data = response.json()
        
        # 检查必要的字段
        assert "status" in data
        assert "version" in data
        assert "timestamp" in data
    
    def test_error_response_structure(self):
        """测试错误响应结构"""
        response = client.get("/api/v1/prescriptions/99999")
        data = response.json()
        
        # 检查错误响应结构
        assert data["code"] == "NOT_FOUND"
        assert "message" in data
        assert "details" in data
        assert "timestamp" in data


class TestCORS:
    """CORS测试"""
    
    def test_cors_headers(self):
        """测试CORS响应头"""
        response = client.options("/health", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET"
        })
        
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers


class TestPerformance:
    """性能测试"""
    
    def test_response_time(self):
        """测试响应时间"""
        import time
        
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        
        response_time = end_time - start_time
        assert response.status_code == 200
        assert response_time < 1.0  # 响应时间应小于1秒
    
    def test_concurrent_requests(self):
        """测试并发请求"""
        import concurrent.futures
        
        def make_request():
            return client.get("/health")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in futures]
        
        # 所有请求都应成功
        assert all(r.status_code == 200 for r in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
