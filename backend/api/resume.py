"""简历解析API路由"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.resume import ResumeService, get_resume_service
from loguru import logger


router = APIRouter()


class ParseResultResponse(BaseModel):
    """解析结果响应"""
    success: bool
    extracted_data: Optional[dict] = None
    resume_text: Optional[str] = None
    file_path: Optional[str] = None
    error: Optional[str] = None


class ConfirmResumeRequest(BaseModel):
    """确认简历解析结果请求"""
    extracted_data: dict


class OneClickJobRequest(BaseModel):
    """一键求职请求"""
    platforms: List[str] = ["boss"]
    auto_apply: bool = False
    max_apply: int = 20
    use_ai_keywords: bool = False


class OneClickJobResponse(BaseModel):
    """一键求职响应"""
    success: bool
    keywords_used: List[str] = []
    total_found: int = 0
    total_applied: int = 0
    error: Optional[str] = None


@router.post("/upload", response_model=ParseResultResponse)
async def upload_and_parse_resume(
    file: UploadFile = File(...),
    use_ai: bool = Query(False, description="是否使用AI模式提取信息"),
    user_id: int = 1,
):
    """
    上传并解析简历

    - 支持 PDF 格式
    - use_ai: 是否使用AI模式（默认规则模式，更快但准确度中等）
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "目前仅支持PDF格式简历")

    # 保存临时文件
    import tempfile
    import os

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        # 解析简历
        service = get_resume_service()
        result = await service.parse_resume_file(
            file_path=tmp_path,
            user_id=user_id,
            use_ai=use_ai,
        )

        # 不删除临时文件，保留给后续使用
        if result.get("success"):
            result["file_path"] = tmp_path

        return result

    except Exception as e:
        logger.error(f"Upload resume error: {e}")
        raise HTTPException(500, f"简历解析失败: {str(e)}")


@router.post("/parse-file", response_model=ParseResultResponse)
async def parse_resume_file(
    file_path: str = Query(..., description="简历文件路径"),
    use_ai: bool = Query(False, description="是否使用AI模式提取信息"),
    user_id: int = 1,
):
    """
    解析指定路径的简历文件

    用于直接解析本地文件，无需上传
    """
    import os

    if not os.path.exists(file_path):
        raise HTTPException(404, f"文件不存在: {file_path}")

    if not file_path.lower().endswith(".pdf"):
        raise HTTPException(400, "目前仅支持PDF格式简历")

    try:
        service = get_resume_service()
        result = await service.parse_resume_file(
            file_path=file_path,
            user_id=user_id,
            use_ai=use_ai,
        )

        return result

    except Exception as e:
        logger.error(f"Parse resume error: {e}")
        raise HTTPException(500, f"简历解析失败: {str(e)}")


@router.get("/status")
async def get_resume_status(
    user_id: int = 1,
):
    """获取简历解析状态"""
    try:
        service = get_resume_service()
        status = service.get_resume_status(user_id)
        return status
    except Exception as e:
        logger.error(f"Get resume status error: {e}")
        raise HTTPException(500, str(e))


@router.get("/download")
async def download_resume(
    user_id: int = 1,
):
    """下载简历文件"""
    from fastapi.responses import FileResponse
    import os

    try:
        service = get_resume_service()
        status = service.get_resume_status(user_id)

        file_path = status.get("resume_file")
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(404, "简历文件不存在")

        return FileResponse(
            path=file_path,
            filename="resume.pdf",
            media_type="application/pdf",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download resume error: {e}")
        raise HTTPException(500, str(e))


@router.put("/confirm")
async def confirm_resume_result(
    request: ConfirmResumeRequest,
    user_id: int = 1,
    db: Session = Depends(get_db),
):
    """
    确认/修改解析结果

    用户可以修改AI提取的信息后再确认保存
    """
    from backend.core.database import UserProfile

    try:
        profile = db.query(UserProfile).filter(UserProfile.id == user_id).first()

        if not profile:
            profile = UserProfile(id=user_id)
            db.add(profile)

        # 更新字段
        data = request.extracted_data
        field_mapping = {
            "name": "name",
            "gender": "gender",
            "age": "age",
            "phone": "phone",
            "email": "email",
            "city": "city",
            "education": "education",
            "school": "school",
            "major": "major",
            "experience_years": "experience_years",
            "target_positions": "target_positions",
            "target_cities": "target_cities",
            "expected_salary_min": "expected_salary_min",
            "expected_salary_max": "expected_salary_max",
            "skills": "skills",
            "certifications": "certifications",
            "work_experiences": "work_experiences",
        }

        for source_field, target_field in field_mapping.items():
            value = data.get(source_field)
            if value is not None:
                setattr(profile, target_field, value)

        db.commit()

        return {"success": True, "message": "简历信息已更新"}

    except Exception as e:
        logger.error(f"Confirm resume error: {e}")
        db.rollback()
        raise HTTPException(500, str(e))


@router.post("/one-click-job", response_model=OneClickJobResponse)
async def one_click_job_search(
    request: OneClickJobRequest,
    user_id: int = 1,
):
    """
    一键启动自动求职

    基于简历信息自动生成搜索关键词，在选定平台搜索并投递职位
    """
    try:
        from backend.services import Orchestrator
        from backend.adapters import Platform

        # 1. 获取用户画像和生成关键词
        service = get_resume_service()
        keyword_result = await service.generate_search_keywords(
            user_id=user_id,
            use_ai=request.use_ai_keywords,
        )

        keywords = keyword_result.get("keywords", [])
        filter_config = keyword_result.get("filter_config", {})

        if not keywords:
            return OneClickJobResponse(
                success=False,
                error="无法生成搜索关键词，请确认简历已正确解析",
            )

        # 2. 初始化协调器
        orchestrator = Orchestrator(use_ai=request.use_ai_keywords)
        await orchestrator.initialize()

        # 3. 执行搜索
        platforms = [Platform(p) for p in request.platforms]
        all_results = []

        for keyword in keywords[:3]:  # 使用前3个关键词
            result = await orchestrator.run_job_search_cycle(
                platforms=platforms,
                keywords=keyword,
                city=filter_config.get("cities", [None])[0],
                apply_filtered=request.auto_apply,
            )
            all_results.append(result)

            # 控制总投递数
            total_applied = sum(r.get("success_count", 0) for r in all_results)
            if total_applied >= request.max_apply:
                break

        # 4. 汇总结果
        total_found = sum(r.get("total_jobs", 0) for r in all_results)
        total_applied = sum(r.get("success_count", 0) for r in all_results)

        return OneClickJobResponse(
            success=True,
            keywords_used=keywords[:3],
            total_found=total_found,
            total_applied=total_applied,
        )

    except Exception as e:
        logger.error(f"One click job error: {e}")
        return OneClickJobResponse(
            success=False,
            error=str(e),
        )