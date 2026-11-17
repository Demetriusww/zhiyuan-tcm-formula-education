"""
方剂服务单元测试
"""
import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from sqlalchemy.orm import Session

from app.services.prescription_service import PrescriptionService
from app.services.llm_service import llm_service
from app.models.schemas import (
    PrescriptionCreate,
    PrescriptionUpdate,
    PrescriptionHerb,
    PrescriptionResponse,
    PrescriptionType
)
from app.core.exceptions import ValidationError, NotFoundError, DuplicateError


class TestPrescriptionService:
    """方剂服务测试类"""
    
    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def service(self, mock_db):
        """创建服务实例"""
        return PrescriptionService(mock_db)
    
    @pytest.fixture
    def sample_herbs(self):
        """示例药物数据"""
        return [
            PrescriptionHerb(herb_id=1, name="人参", dosage="9g", order=1),
            PrescriptionHerb(herb_id=2, name="白术", dosage="9g", order=2),
            PrescriptionHerb(herb_id=3, name="茯苓", dosage="9g", order=3),
        ]
    
    @pytest.fixture
    def sample_prescription_data(self, sample_herbs):
        """示例方剂创建数据"""
        return PrescriptionCreate(
            name="四君子汤",
            pinyin="Si Jun Zi Tang",
            type=PrescriptionType.CLASSIC,
            source="《太平惠民和剂局方》",
            functions="益气健脾",
            indications="脾胃气虚证",
            herbs=sample_herbs
        )
    
    @pytest.mark.asyncio
    async def test_create_prescription_success(self, service, mock_db, sample_prescription_data):
        """测试成功创建方剂"""
        # 模拟数据库查询结果
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.flush = Mock()
        mock_db.commit = Mock()
        
        # 模拟药物验证
        with patch.object(service, '_validate_herbs', return_value=None):
            with patch.object(service, 'get_prescription') as mock_get:
                mock_get.return_value = Mock(id=1, name="四君子汤")
                
                result = await service.create_prescription(sample_prescription_data)
                
                assert result is not None
                mock_db.add.assert_called()
                mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_prescription_duplicate(self, service, mock_db, sample_prescription_data):
        """测试创建重复方剂"""
        # 模拟已存在同名方剂
        existing = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = existing
        
        with pytest.raises(DuplicateError) as exc_info:
            await service.create_prescription(sample_prescription_data)
        
        assert "已存在" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_create_prescription_invalid_herbs_count(self, service, mock_db):
        """测试创建方剂时药物数量不足"""
        # 只有1味药
        invalid_data = PrescriptionCreate.model_construct(
            name="测试方",
            herbs=[PrescriptionHerb(herb_id=1, name="人参", dosage="9g", order=1)],
        )
        
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(ValidationError) as exc_info:
            await service.create_prescription(invalid_data)
        
        assert "至少" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_prescription_success(self, service, mock_db):
        """测试成功获取方剂"""
        # 模拟数据库中的方剂
        mock_prescription = Mock()
        mock_prescription.id = 1
        mock_prescription.name = "四君子汤"
        mock_prescription.herbs = []
        mock_prescription.pinyin = None
        mock_prescription.type = "经典名方"
        mock_prescription.source = None
        mock_prescription.functions = None
        mock_prescription.indications = None
        mock_prescription.usage = None
        mock_prescription.precautions = None
        mock_prescription.category = None
        mock_prescription.created_at = datetime.now()
        mock_prescription.updated_at = datetime.now()
        
        mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = mock_prescription

        result = await service.get_prescription(1)

        assert result.id == 1
        assert result.name == "四君子汤"
    
    @pytest.mark.asyncio
    async def test_get_prescription_not_found(self, service, mock_db):
        """测试获取不存在的方剂"""
        mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(NotFoundError) as exc_info:
            await service.get_prescription(999)
        
        assert "不存在" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_update_prescription_success(self, service, mock_db):
        """测试成功更新方剂"""
        # 模拟现有方剂
        mock_prescription = Mock()
        mock_prescription.id = 1
        mock_prescription.name = "四君子汤"
        
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_prescription,
            None,
        ]
        mock_db.query.return_value.filter.return_value.filter.return_value.first.return_value = None
        
        update_data = PrescriptionUpdate(name="新四君子汤")
        
        with patch.object(service, 'get_prescription') as mock_get:
            mock_get.return_value = PrescriptionResponse.model_construct(
                id=1,
                name="新四君子汤",
                pinyin=None,
                category=None,
                type=None,
                efficacy=None,
                indications=None,
                usage=None,
                contraindications=None,
                source=None,
                notes=None,
                herbs=[],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            
            result = await service.update_prescription(1, update_data)
            
            assert result.name == "新四君子汤"
            mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_prescription_success(self, service, mock_db):
        """测试成功删除方剂"""
        mock_prescription = Mock()
        mock_prescription.id = 1
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_prescription
        
        result = await service.delete_prescription(1)
        
        assert result is True
        mock_db.delete.assert_called_once_with(mock_prescription)
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_compatibility(self, service, mock_db):
        """测试配伍分析"""
        # 模拟方剂数据
        mock_prescription = Mock()
        mock_prescription.id = 1
        mock_prescription.name = "四君子汤"
        mock_prescription.herbs = [
            PrescriptionHerb(herb_id=1, name="人参", dosage="9g", order=1)
        ]
        
        with patch.object(service, 'get_prescription', return_value=mock_prescription):
            # 模拟LLM服务
            mock_analysis = Mock()
            mock_analysis.overall_score = 85
            
            with patch.object(llm_service, 'analyze_compatibility', return_value=mock_analysis):
                result = await service.analyze_compatibility(1)
                
                assert result.overall_score == 85
    
    @pytest.mark.asyncio
    async def test_compare_prescriptions_success(self, service, mock_db):
        """测试成功对比方剂"""
        # 模拟两个方剂
        mock_prescription1 = PrescriptionResponse(
            id=1,
            name="方剂1",
            type=PrescriptionType.CLASSIC,
            functions="益气健脾",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            herbs=[
                PrescriptionHerb(herb_id=1, name="人参", dosage="9g", order=1),
                PrescriptionHerb(herb_id=2, name="白术", dosage="9g", order=2),
            ],
        )
        mock_prescription2 = PrescriptionResponse(
            id=2,
            name="方剂2",
            type=PrescriptionType.CLASSIC,
            functions="益气健脾",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            herbs=[
                PrescriptionHerb(herb_id=1, name="人参", dosage="9g", order=1),
                PrescriptionHerb(herb_id=2, name="白术", dosage="9g", order=2),
                PrescriptionHerb(herb_id=3, name="茯苓", dosage="9g", order=3),
            ],
        )
        
        with patch.object(service, 'get_prescription') as mock_get:
            mock_get.side_effect = [mock_prescription1, mock_prescription2]
            
            result = await service.compare_prescriptions([1, 2])
            
            assert len(result.prescriptions) == 2
            assert result.recommendation is not None
    
    @pytest.mark.asyncio
    async def test_compare_prescriptions_insufficient(self, service, mock_db):
        """测试对比方剂数量不足"""
        with pytest.raises(ValidationError) as exc_info:
            await service.compare_prescriptions([1])
        
        assert "至少" in str(exc_info.value)


class TestPrescriptionValidation:
    """方剂验证测试类"""
    
    def test_prescription_create_validation(self):
        """测试方剂创建数据验证"""
        # 有效数据
        valid_data = PrescriptionCreate(
            name="测试方",
            herbs=[
                PrescriptionHerb(herb_id=1, name="药1", dosage="9g", order=1),
                PrescriptionHerb(herb_id=2, name="药2", dosage="9g", order=2)
            ]
        )
        assert valid_data.name == "测试方"
        assert len(valid_data.herbs) == 2
    
    def test_prescription_herb_validation(self):
        """测试药物数据验证"""
        herb = PrescriptionHerb(
            herb_id=1,
            name="人参",
            dosage="9g",
            preparation="切片",
            order=1
        )
        
        assert herb.name == "人参"
        assert herb.dosage == "9g"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
