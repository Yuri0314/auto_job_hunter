# 简历列表批量删除功能设计

## 背景

用户需要在简历列表页支持批量删除操作，避免逐个删除多条简历的重复操作。

## 设计方案

采用常驻复选框方案：每行简历左侧始终显示复选框，用户勾选后可批量删除。

### 前端改动

**文件**: `frontend/pages/resume_manager.py`

1. **添加复选框状态管理**
   - `st.session_state.selected_resumes`: Set[int]，存储选中简历ID

2. **UI结构改动**
   - 列表顶部添加工具栏：
     - "全选"按钮：选中/取消选中全部简历
     - "批量删除"按钮：仅当选中数量>0时显示，显示选中数量
   - 每行卡片左侧添加复选框（`st.checkbox`）

3. **删除确认流程**
   - 点击"批量删除"后显示确认弹窗（使用 `st.warning` + 确认/取消按钮）
   - 弹窗显示：`确认删除 X 条简历？此操作不可撤销`
   - 确认后调用API，成功则刷新列表

4. **按钮布局**
   ```
   [全选]  [批量删除 (N)]    [刷新列表]

   ☑ Python后端简历.pdf ⭐主简历    [查看] [编辑] [删除]
   ☐ 前端简历.docx                [查看] [编辑] [设为主简历] [删除]
   ☑ 测试简历.md                  [查看] [编辑] [设为主简历] [删除]
   ```

### 后端改动

**文件**: `backend/api/resume.py`

新增API端点：

```python
class BatchDeleteRequest(BaseModel):
    ids: List[int]

@router.post("/batch-delete")
async def batch_delete_resumes(
    request: BatchDeleteRequest,
    db: Session = Depends(get_db),
):
    """批量删除简历"""
    from backend.core.database import Resume

    deleted = 0
    for resume_id in request.ids:
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if resume:
            db.delete(resume)
            deleted += 1

    db.commit()
    return {"success": True, "deleted": deleted}
```

### 数据流

```
用户勾选复选框 → 更新 session_state.selected_resumes
点击批量删除 → 显示确认弹窗
确认 → POST /api/resume/batch-delete {"ids": [...]}
API返回 → 清空选中状态，刷新列表，显示成功消息
```

### 边界情况

- **删除主简历**: 允许删除，删除后该用户无主简历状态
- **部分删除失败**: API返回成功删除数量，前端显示
- **空选择**: 批量删除按钮不显示或禁用

## 实施范围

- 前端: `frontend/pages/resume_manager.py` (~50行改动)
- 后端: `backend/api/resume.py` (~15行新增)
- 无数据库改动
- 无新依赖

## 测试要点

1. 单条删除仍正常工作
2. 批量删除确认弹窗正确显示数量
3. 全选/取消全选正常
4. 删除后列表正确刷新
5. API层：空列表、不存在ID的处理