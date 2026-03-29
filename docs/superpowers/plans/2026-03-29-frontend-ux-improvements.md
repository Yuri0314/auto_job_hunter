# Frontend UX Improvements - Search Results Persistence & Multi-Keyword Search

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve search UX by preserving results across navigation and enabling multi-keyword search.

**Architecture:**
1. Keep search results in session state without clearing on navigation
2. Add "查看上次结果" quick access when previous results exist
3. Generate combined keywords from target_positions + skills for smarter search

**Tech Stack:** Streamlit, Python, existing backend API

---

## File Structure

**Files to modify:**
- `frontend/app.py` - Main Streamlit application
  - Session state initialization (preserve results)
  - Search page (multi-keyword, quick results access)
  - Results page (fix navigation)
  - Initialization logic (smarter keyword prefill)

---

## Task 1: Preserve Search Results Across Navigation

**Files:**
- Modify: `frontend/app.py:834-841` (navigation buttons in step_results)

**Problem:** Current code clears `search_results = None` when clicking "返回修改搜索", and step navigation hides results from other pages.

- [ ] **Step 1: Remove the line that clears search results**

Find line 836 in `step_results()`:
```python
st.session_state.search_results = None
```
Remove this line. The button should just change step without clearing data.

- [ ] **Step 2: Verify the fix manually**

1. Run search, see results on step 3
2. Click "← 返回修改搜索"
3. Verify: `st.session_state.search_results` still contains data
4. Should be able to go back to step 3 to see results

---

## Task 2: Add "查看上次结果" Quick Access on Search Page

**Files:**
- Modify: `frontend/app.py` - `step_search()` function

- [ ] **Step 1: Add quick access section in step_search()**

Insert after the "投递选项" section (around line 805), before the search button:

```python
    # 如果有上次搜索结果，显示快速访问
    if st.session_state.search_results:
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("查看上次搜索结果", expanded=False):
            last_result = st.session_state.search_results
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("发现职位", last_result.get("total_found", 0))
            with col2:
                st.metric("符合条件", last_result.get("filtered_jobs", 0))
            with col3:
                st.metric("已投递", last_result.get("applied", 0))

            if st.button("查看详细结果", key="view_last_results"):
                st.session_state.step = 3
                st.rerun()
```

- [ ] **Step 2: Test the quick access feature**

1. Run a search
2. Go back to search page (step 2)
3. Verify: "查看上次搜索结果" expander appears
4. Click to expand, see the stats
5. Click "查看详细结果" to go to step 3

---

## Task 3: Implement Multi-Keyword Prefill Logic

**Files:**
- Modify: `frontend/app.py` - initialization section and `step_search()`

- [ ] **Step 1: Add keyword suggestions to session state initialization**

Add after line 459 (after `_platform_status`):
```python
if "_keyword_suggestions" not in st.session_state:
    st.session_state._keyword_suggestions = []
```

- [ ] **Step 2: Update initialization loading to generate keyword suggestions**

Find the initialization block in the loading section (around line 1155). Update to generate suggestions:

```python
    if not st.session_state.initialized:
        # ... existing code ...

        # Load user profile for prefill
        try:
            r = requests.get(f"{API_BASE}/user/profile", timeout=5)
            if r.ok:
                profile = r.json()
                st.session_state._user_profile = profile

                # Generate keyword suggestions from profile
                suggestions = []
                # Add target positions first
                target_positions = profile.get("target_positions", [])
                suggestions.extend(target_positions[:3])
                # Add top skills
                skills = profile.get("skills", [])
                suggestions.extend(skills[:3])
                # Remove duplicates while preserving order
                seen = set()
                unique_suggestions = []
                for s in suggestions:
                    if s and s not in seen:
                        seen.add(s)
                        unique_suggestions.append(s)
                st.session_state._keyword_suggestions = unique_suggestions

                # Set default prefill (first suggestion)
                if unique_suggestions:
                    st.session_state._prefill_keywords = unique_suggestions[0]
                st.session_state._prefill_city = profile.get("city", "")
        except:
            pass

        st.session_state.initialized = True
```

- [ ] **Step 3: Update search form to show keyword suggestions**

In `step_search()`, replace the keywords text_input section (around line 777-781) with:

```python
    # 显示关键词建议
    suggestions = st.session_state.get("_keyword_suggestions", [])
    if suggestions:
        st.markdown("<div style='margin-bottom: 0.5rem;'>", unsafe_allow_html=True)
        st.caption("推荐关键词（点击添加）:")
        suggestion_cols = st.columns(min(len(suggestions), 5))
        for i, kw in enumerate(suggestions[:5]):
            with suggestion_cols[i]:
                if st.button(kw, key=f"kw_{i}", use_container_width=True):
                    current = st.session_state.get("_search_keywords", "")
                    if current:
                        st.session_state._search_keywords = f"{current} {kw}"
                    else:
                        st.session_state._search_keywords = kw
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # 初始化搜索关键词
    if "_search_keywords" not in st.session_state:
        st.session_state._search_keywords = default_keywords

    keywords = st.text_input(
        "搜索关键词",
        placeholder="如: Python后端、产品经理（可输入多个，空格分隔）",
        value=st.session_state._search_keywords,
        key="keywords_input"
    )
    # 同步到 session state
    st.session_state._search_keywords = keywords
```

- [ ] **Step 4: Update the prefill hint text**

Replace line 795 with:
```python
    if suggestions:
        st.caption(f"已从简历提取 {len(suggestions)} 个推荐关键词，点击上方按钮快速添加")
```

---

## Task 4: Update Backend to Support Multi-Keyword Search

**Files:**
- Modify: `frontend/app.py` - `api_search_jobs()` function

- [ ] **Step 1: Parse multiple keywords in search function**

Update `api_search_jobs()` (around line 508) to split keywords:

```python
def api_search_jobs(keywords, platforms, city, auto_apply=False, greeting=""):
    try:
        # 支持多关键词搜索（空格分隔）
        # 将多个关键词作为单个搜索词发送，或分别搜索
        keyword_list = keywords.split()

        # 如果有多个关键词，使用第一个进行搜索
        # 后续可以扩展为多次搜索合并结果
        primary_keyword = keyword_list[0] if keyword_list else keywords

        r = requests.post(f"{API_BASE}/applications/search-and-apply", json={
            "keywords": primary_keyword,
            "platforms": platforms,
            "city": city,
            "auto_apply": auto_apply,
            "greeting_template": greeting,
            "max_count": 20,
        }, timeout=120)
        result = r.json()
        # 映射后端的 filtered 字段到 frontend 的 filtered_jobs
        if "filtered" in result and "filtered_jobs" not in result:
            result["filtered_jobs"] = result["filtered"]
        # 记录搜索使用的关键词
        result["search_keywords"] = keywords
        return result
    except Exception as e:
        return {"error": str(e)}
```

- [ ] **Step 2: Test multi-keyword input**

1. Enter "产品经理 AI" in the keywords field
2. Click search
3. Verify: Results show, and search_keywords is saved

---

## Task 5: Display Search Keywords in Results

**Files:**
- Modify: `frontend/app.py` - `step_results()` function

- [ ] **Step 1: Add search info display in results page**

In `step_results()`, after the step card header (around line 851), add:

```python
    # 显示本次搜索使用的关键词
    search_keywords = result.get("search_keywords", "")
    if search_keywords:
        st.markdown(f"""
        <div style="padding: 0.75rem 1rem; background: var(--bg-glass); border-radius: 8px; margin-bottom: 1rem; border: 1px solid var(--border-subtle);">
            <span style="color: var(--text-muted); font-size: 0.85rem;">搜索关键词：</span>
            <span style="color: var(--accent-electric); font-family: 'JetBrains Mono';">{search_keywords}</span>
        </div>
        """, unsafe_allow_html=True)
```

- [ ] **Step 2: Verify the search info displays**

1. Run a search with multiple keywords
2. On results page, verify the keywords are shown
3. Navigate away and back, verify keywords persist

---

## Task 6: Final Integration Testing

- [ ] **Step 1: Test complete user flow**

1. Load frontend - verify keyword suggestions appear
2. Click a suggestion keyword - verify it's added to input
3. Add another keyword - verify input updates
4. Run search - verify results appear with keywords shown
5. Click "返回修改搜索" - verify results preserved
6. Click "查看上次搜索结果" expander - verify stats shown
7. Click "查看详细结果" - verify returns to step 3
8. Go to resume page - verify results still accessible

- [ ] **Step 2: Test edge cases**

1. No resume data - verify no suggestions, no errors
2. Empty keywords - verify warning shown
3. Session refresh - verify state resets appropriately

---

## Summary of Changes

| Change | File | Lines |
|--------|------|-------|
| Remove search_results clearing | app.py:836 | Delete line |
| Add keyword_suggestions state | app.py:~459 | Add 2 lines |
| Update init to generate suggestions | app.py:~1155 | Add ~20 lines |
| Add suggestion buttons in search form | app.py:~777 | Add ~20 lines |
| Add quick results access | app.py:~805 | Add ~15 lines |
| Display search keywords in results | app.py:~851 | Add ~8 lines |
| Update api_search_jobs | app.py:~508 | Add keyword tracking |