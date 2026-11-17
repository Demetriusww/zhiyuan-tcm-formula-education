"""方剂 API 路由。"""
from datetime import datetime
from typing import Literal, Optional

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.cache import (
    cache,
    invalidate_prescription_cache,
    prescription_list_key,
)
from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.database_models import User
from app.models.schemas import (
    APIResponse,
    PaginationParams,
    PrescriptionCompareRequest,
    PrescriptionCreate,
    PrescriptionOptimizeRequest,
    PrescriptionType,
    PrescriptionUpdate,
)
from app.services.prescription_io_service import PrescriptionIOService
from app.services.prescription_service import PrescriptionService

router = APIRouter(tags=["方剂管理"])


def get_prescription_service(db: Session = Depends(get_db)) -> PrescriptionService:
    return PrescriptionService(db)


def _response(message: str, data=None) -> APIResponse:
    return APIResponse(message=message, data=data)


@router.post(
    "",
    response_model=APIResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建方剂",
)
async def create_prescription(
    prescription_data: PrescriptionCreate,
    current_user: User = Depends(get_current_user),
    service: PrescriptionService = Depends(get_prescription_service),
):
    result = await service.create_prescription(prescription_data)
    await invalidate_prescription_cache(result.id)
    return _response("方剂创建成功", result)


@router.get("", response_model=APIResponse, summary="获取方剂列表")
async def list_prescriptions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=500),
    keyword: Optional[str] = Query(None, description="搜索名称、功效、主治"),
    name: Optional[str] = Query(None, description="名称模糊筛选"),
    type: Optional[PrescriptionType] = Query(None, description="方剂类型"),
    category: Optional[str] = Query(None, description="方剂分类"),
    sort_by: Literal["name", "created_at", "updated_at"] = Query("updated_at"),
    sort_order: Literal["asc", "desc"] = Query("desc"),
    service: PrescriptionService = Depends(get_prescription_service),
):
    filters = {
        "keyword": keyword,
        "name": name,
        "type": type.value if type else None,
        "category": category,
    }
    cache_key = prescription_list_key(
        page,
        page_size,
        keyword,
        name,
        filters["type"],
        category,
        sort_by,
        sort_order,
    )
    cached = await cache.get_json(cache_key)
    if cached is not None:
        return _response("获取成功", cached)
    result = await service.list_prescriptions(
        PaginationParams(page=page, page_size=page_size),
        filters,
        sort_by,
        sort_order,
    )
    await cache.set_json(
        cache_key,
        result.model_dump(mode="json"),
        settings.CACHE_SEARCH_TIMEOUT,
    )
    return _response("获取成功", result)


@router.get("/search", response_model=APIResponse, summary="搜索方剂")
async def search_prescriptions(
    query: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=500),
    sort_by: Literal["name", "created_at", "updated_at"] = Query("updated_at"),
    sort_order: Literal["asc", "desc"] = Query("desc"),
    service: PrescriptionService = Depends(get_prescription_service),
):
    cache_key = prescription_list_key(
        page, page_size, query, None, None, None, sort_by, sort_order
    )
    cached = await cache.get_json(cache_key)
    if cached is not None:
        return _response("搜索成功", cached)
    result = await service.list_prescriptions(
        PaginationParams(page=page, page_size=page_size),
        {"keyword": query},
        sort_by,
        sort_order,
    )
    await cache.set_json(
        cache_key,
        result.model_dump(mode="json"),
        settings.CACHE_SEARCH_TIMEOUT,
    )
    return _response("搜索成功", result)


@router.post("/import", response_model=APIResponse, summary="批量导入方剂")
async def import_prescriptions(
    file: UploadFile = File(...),
    upload_format: str = Form("auto", alias="format"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    content = await file.read()
    service = PrescriptionIOService(db)
    result = await service.import_file(
        filename=file.filename or "",
        content=content,
        format_hint=upload_format,
    )
    if result.get("created", 0):
        await invalidate_prescription_cache()
    return _response("导入完成", result)


@router.get("/export", summary="批量导出方剂")
async def export_prescriptions(
    format: Literal["json", "xlsx"] = Query("json"),
    keyword: Optional[str] = Query(None),
    name: Optional[str] = Query(None),
    type: Optional[PrescriptionType] = Query(None),
    category: Optional[str] = Query(None),
    sort_by: Literal["name", "created_at", "updated_at"] = Query("updated_at"),
    sort_order: Literal["asc", "desc"] = Query("desc"),
    service: PrescriptionService = Depends(get_prescription_service),
):
    items = await service.get_all_prescriptions(
        {
            "keyword": keyword,
            "name": name,
            "type": type.value if type else None,
            "category": category,
        },
        sort_by,
        sort_order,
    )
    io_service = PrescriptionIOService(service.db)
    content = (
        io_service.export_json(items)
        if format == "json"
        else io_service.export_xlsx(items)
    )
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"prescriptions_{timestamp}.{format}"
    media_type = (
        "application/json"
        if format == "json"
        else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    return StreamingResponse(
        iter([content]),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/compare", response_model=APIResponse, summary="方剂对比")
async def compare_prescriptions(
    request: PrescriptionCompareRequest,
    service: PrescriptionService = Depends(get_prescription_service),
):
    result = await service.compare_prescriptions(request.prescription_ids)
    return _response("对比完成", result)


@router.get("/{prescription_id}", response_model=APIResponse, summary="获取方剂详情")
async def get_prescription(
    prescription_id: int,
    service: PrescriptionService = Depends(get_prescription_service),
):
    cache_key = f"prescriptions:detail:{prescription_id}"
    cached = await cache.get_json(cache_key)
    if cached is not None:
        return _response("获取成功", cached)
    result = await service.get_prescription(prescription_id)
    await cache.set_json(
        cache_key,
        result.model_dump(mode="json"),
        settings.CACHE_PRESCRIPTION_TIMEOUT,
    )
    return _response("获取成功", result)


@router.put("/{prescription_id}", response_model=APIResponse, summary="更新方剂")
async def update_prescription(
    prescription_id: int,
    update_data: PrescriptionUpdate,
    current_user: User = Depends(get_current_user),
    service: PrescriptionService = Depends(get_prescription_service),
):
    result = await service.update_prescription(prescription_id, update_data)
    await invalidate_prescription_cache(prescription_id)
    return _response("方剂更新成功", result)


@router.delete("/{prescription_id}", response_model=APIResponse, summary="删除方剂")
async def delete_prescription(
    prescription_id: int,
    current_user: User = Depends(get_current_user),
    service: PrescriptionService = Depends(get_prescription_service),
):
    await service.delete_prescription(prescription_id)
    await invalidate_prescription_cache(prescription_id)
    return _response("方剂删除成功", None)


@router.post("/{prescription_id}/analyze", response_model=APIResponse, summary="配伍分析")
async def analyze_compatibility(
    prescription_id: int,
    service: PrescriptionService = Depends(get_prescription_service),
):
    cache_key = f"prescriptions:analysis:{prescription_id}"
    cached = await cache.get_json(cache_key)
    if cached is not None:
        return _response("分析完成", cached)
    result = await service.analyze_compatibility(prescription_id)
    await cache.set_json(
        cache_key,
        result.model_dump(mode="json"),
        settings.CACHE_ANALYSIS_TIMEOUT,
    )
    return _response("分析完成", result)


@router.post("/{prescription_id}/optimize", response_model=APIResponse, summary="方剂优化")
async def optimize_prescription(
    prescription_id: int,
    request: PrescriptionOptimizeRequest,
    service: PrescriptionService = Depends(get_prescription_service),
):
    result = await service.optimize_prescription(
        prescription_id,
        request.target_symptoms,
    )
    return _response("优化完成", result)
