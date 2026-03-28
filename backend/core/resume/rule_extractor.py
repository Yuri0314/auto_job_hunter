"""规则模式简历信息提取器（无AI）"""

import re
from typing import Dict, Any, List, Optional
from loguru import logger


class RuleExtractor:
    """基于规则的简历信息提取器"""

    # 常见城市列表
    CITIES = [
        "北京", "上海", "广州", "深圳", "杭州", "南京", "苏州", "成都", "武汉",
        "西安", "重庆", "天津", "长沙", "郑州", "青岛", "厦门", "宁波", "无锡",
        "合肥", "福州", "大连", "沈阳", "哈尔滨", "济南", "东莞", "佛山", "珠海",
        "中山", "惠州", "昆明", "贵阳", "南昌", "太原", "石家庄", "南宁", "兰州",
    ]

    # 学历关键词
    EDUCATIONS = ["博士", "硕士", "本科", "大专", "专科", "高中", "中专", "研究生"]

    # 常见技术技能关键词
    TECH_SKILLS = [
        # 编程语言
        "Python", "Java", "JavaScript", "JS", "TypeScript", "TS", "Go", "Golang",
        "C++", "C#", "PHP", "Ruby", "Rust", "Kotlin", "Swift", "Scala",
        "C语言", "Go语言", "Python语言",

        # 前端
        "Vue", "React", "Angular", "HTML", "CSS", "Node.js", "Nodejs",
        "前端", "后端", "全栈", "小程序", "React Native", "Flutter",

        # 后端框架
        "Django", "Flask", "FastAPI", "Spring", "SpringBoot", "Spring Boot",
        "Express", "Koa", "Gin", "Echo", "MyBatis", "Hibernate",

        # 数据库
        "MySQL", "PostgreSQL", "MongoDB", "Redis", "Oracle", "SQL Server",
        "SQLite", "Elasticsearch", "ES", "ClickHouse", "数据库",

        # 大数据
        "Hadoop", "Spark", "Flink", "Kafka", "Hive", "HBase", "Presto",
        "数据仓库", "ETL", "大数据",

        # 云原生 & DevOps
        "Docker", "Kubernetes", "K8s", "Jenkins", "Git", "CI/CD", "Linux",
        "Nginx", "Tomcat", "Ansible", "Terraform", "云原生", "容器",

        # AI/ML
        "机器学习", "深度学习", "人工智能", "AI", "ML", "DL",
        "TensorFlow", "PyTorch", "Keras", "Scikit-learn", "sklearn",
        "NLP", "CV", "计算机视觉", "自然语言处理", "LLM", "GPT",

        # 移动开发
        "Android", "iOS", "鸿蒙", "HarmonyOS",

        # 测试
        "自动化测试", "测试开发", "Selenium", "Pytest", "JUnit", "性能测试",

        # 其他
        "微服务", "分布式", "高并发", "系统设计", "架构", "敏捷开发", "Scrum",
        "SQL", "RESTful", "API", "WebSocket", "RPC", "gRPC",
        "OAuth", "JWT", "设计模式", "算法", "数据结构",
    ]

    # 职位类型关键词
    POSITION_KEYWORDS = [
        "后端", "前端", "全栈", "架构师", "技术经理", "技术总监",
        "Java开发", "Python开发", "Go开发", "前端开发", "后端开发",
        "数据开发", "数据分析师", "算法工程师", "AI工程师", "机器学习",
        "测试工程师", "运维工程师", "DevOps", "产品经理", "项目经理",
        "移动开发", "Android开发", "iOS开发", "嵌入式", "硬件",
        "安全工程师", "网络工程师", "数据库管理员", "DBA",
    ]

    def extract(self, text: str) -> Dict[str, Any]:
        """
        从简历文本中提取关键信息

        Args:
            text: 简历文本

        Returns:
            提取的信息字典
        """
        logger.info("开始规则模式提取简历信息")

        result = {
            "name": self._extract_name(text),
            "gender": self._extract_gender(text),
            "age": self._extract_age(text),
            "phone": self._extract_phone(text),
            "email": self._extract_email(text),
            "city": self._extract_city(text),
            "education": self._extract_education(text),
            "school": self._extract_school(text),
            "major": self._extract_major(text),
            "experience_years": self._extract_experience_years(text),
            "target_positions": self._extract_target_positions(text),
            "target_cities": self._extract_target_cities(text),
            "expected_salary_min": None,
            "expected_salary_max": None,
            "skills": self._extract_skills(text),
            "certifications": self._extract_certifications(text),
            "work_experiences": self._extract_work_experiences(text),
            "summary": self._extract_summary(text),
        }

        # 提取期望薪资
        salary = self._extract_expected_salary(text)
        if salary:
            result["expected_salary_min"] = salary[0]
            result["expected_salary_max"] = salary[1]

        # 记录提取结果
        extracted_fields = [k for k, v in result.items() if v is not None and v != []]
        logger.info(f"规则提取完成，成功提取 {len(extracted_fields)} 个字段: {extracted_fields}")

        return result

    def _extract_name(self, text: str) -> Optional[str]:
        """提取姓名"""
        lines = text.strip().split("\n")

        # 通常姓名在简历开头
        for line in lines[:5]:
            line = line.strip()
            # 姓名通常是2-4个中文字符，不含特殊字符
            if re.match(r"^[\u4e00-\u9fa5]{2,4}$", line):
                return line

        # 尝试匹配 "姓名：xxx" 格式
        match = re.search(r"姓\s*名\s*[:：]\s*([^\s]+)", text)
        if match:
            return match.group(1).strip()

        return None

    def _extract_gender(self, text: str) -> Optional[str]:
        """提取性别"""
        # 匹配 "男" 或 "女"
        if re.search(r"[,，\s](男)[,，\s]", text) or re.search(r"性\s*别\s*[:：]\s*男", text):
            return "男"
        if re.search(r"[,，\s](女)[,，\s]", text) or re.search(r"性\s*别\s*[:：]\s*女", text):
            return "女"
        return None

    def _extract_age(self, text: str) -> Optional[int]:
        """提取年龄"""
        # 匹配 "27岁" 或 "年龄：27"
        match = re.search(r"(\d{1,2})\s*岁", text)
        if match:
            return int(match.group(1))

        match = re.search(r"年\s*龄\s*[:：]\s*(\d{1,2})", text)
        if match:
            return int(match.group(1))

        # 从出生日期推算
        match = re.search(r"(\d{4})\s*年\s*(\d{1,2})\s*月", text)
        if match:
            from datetime import datetime
            birth_year = int(match.group(1))
            current_year = datetime.now().year
            age = current_year - birth_year
            if 18 <= age <= 60:
                return age

        return None

    def _extract_phone(self, text: str) -> Optional[str]:
        """提取手机号"""
        # 匹配11位手机号
        match = re.search(r"1[3-9]\d{9}", text)
        if match:
            return match.group(0)

        # 匹配带分隔符的号码
        match = re.search(r"1[3-9]\d[\s-]?\d{4}[\s-]?\d{4}", text)
        if match:
            return re.sub(r"[\s-]", "", match.group(0))

        return None

    def _extract_email(self, text: str) -> Optional[str]:
        """提取邮箱"""
        match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
        return match.group(0) if match else None

    def _extract_city(self, text: str) -> Optional[str]:
        """提取所在城市"""
        for city in self.CITIES:
            if city in text:
                return city
        return None

    def _extract_education(self, text: str) -> Optional[str]:
        """提取学历"""
        for edu in self.EDUCATIONS:
            if edu in text:
                return edu
        return None

    def _extract_school(self, text: str) -> Optional[str]:
        """提取毕业院校"""
        # 匹配常见格式
        patterns = [
            r"毕\s*业\s*[:：]\s*([^\n]+)",
            r"院\s*校\s*[:：]\s*([^\n]+)",
            r"学\s*校\s*[:：]\s*([^\n]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                school = match.group(1).strip()
                # 清理多余内容
                school = re.split(r"[,，、\s]", school)[0]
                return school

        return None

    def _extract_major(self, text: str) -> Optional[str]:
        """提取专业"""
        patterns = [
            r"专\s*业\s*[:：]\s*([^\n]+)",
            r"专\s*业\s*[:：]?\s*([^\n,，]+?)(?:\s|,|，|\n)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                major = match.group(1).strip()
                if len(major) < 20:  # 专业名通常不会太长
                    return major

        return None

    def _extract_experience_years(self, text: str) -> Optional[int]:
        """提取工作年限"""
        # 匹配 "X年工作经验" 或 "X年经验"
        match = re.search(r"(\d{1,2})\s*年\s*(?:工作)?经\s*验", text)
        if match:
            return int(match.group(1))

        # 匹配工作经历的时间跨度
        work_years = re.findall(r"(\d{4})\s*[-–至到]", text)
        if len(work_years) >= 2:
            try:
                from datetime import datetime
                years = [int(y) for y in work_years]
                span = max(years) - min(years)
                if 0 < span <= 30:
                    return span
            except:
                pass

        return None

    def _extract_target_positions(self, text: str) -> List[str]:
        """提取目标职位"""
        positions = []

        # 匹配求职意向相关
        match = re.search(r"求\s*职\s*意\s*向\s*[:：]?\s*([^\n]+)", text)
        if match:
            intent = match.group(1)
            for keyword in self.POSITION_KEYWORDS:
                if keyword in intent:
                    positions.append(keyword)

        # 从工作经历推断
        if not positions:
            for keyword in self.POSITION_KEYWORDS:
                if keyword in text:
                    positions.append(keyword)

        return list(set(positions))[:5]  # 去重，最多5个

    def _extract_target_cities(self, text: str) -> List[str]:
        """提取目标城市"""
        cities = []

        # 从求职意向提取
        match = re.search(r"期望\s*(?:城市|地点|工作地)[:：]?\s*([^\n]+)", text)
        if match:
            intent = match.group(1)
            for city in self.CITIES:
                if city in intent:
                    cities.append(city)

        # 使用当前城市
        if not cities:
            current_city = self._extract_city(text)
            if current_city:
                cities.append(current_city)

        return cities

    def _extract_expected_salary(self, text: str) -> Optional[tuple]:
        """提取期望薪资"""
        # 匹配 "15-25K" 或 "15K-25K" 或 "15-25万"
        match = re.search(r"(\d{1,3})\s*[Kk万]?\s*[-–至到]\s*(\d{1,3})\s*[Kk万]?", text)
        if match:
            min_sal = int(match.group(1))
            max_sal = int(match.group(2))
            return (min_sal, max_sal)

        # 匹配 "期望薪资：15-25K"
        match = re.search(r"期望\s*(?:薪资|月薪)[:：]?\s*(\d{1,3})\s*[-–至到]\s*(\d{1,3})\s*[Kk]?", text)
        if match:
            return (int(match.group(1)), int(match.group(2)))

        return None

    def _extract_skills(self, text: str) -> List[str]:
        """提取技能"""
        skills = []

        for skill in self.TECH_SKILLS:
            if skill.lower() in text.lower() or skill in text:
                skills.append(skill)

        # 按出现顺序排序（去重）
        seen = set()
        unique_skills = []
        for skill in skills:
            skill_lower = skill.lower()
            if skill_lower not in seen:
                seen.add(skill_lower)
                unique_skills.append(skill)

        return unique_skills[:20]  # 最多20个技能

    def _extract_certifications(self, text: str) -> List[str]:
        """提取证书"""
        certs = []

        # 匹配证书相关
        patterns = [
            r"证\s*书\s*[:：]?\s*([^\n]+)",
            r"资\s*格\s*[:：]?\s*([^\n]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                cert_text = match.group(1)
                # 分割多个证书
                cert_list = re.split(r"[,，、；;]", cert_text)
                for cert in cert_list:
                    cert = cert.strip()
                    if cert and len(cert) < 30:
                        certs.append(cert)

        return certs

    def _extract_work_experiences(self, text: str) -> List[Dict[str, str]]:
        """提取工作经历"""
        experiences = []

        # 尝试匹配工作经历区块
        # 格式：公司名 + 职位 + 时间
        patterns = [
            r"([^\n]+?)\s*[-–至到]\s*([^\n]+?)\s*\n([^\n]+?公司[^\n]*)",
            r"([^\n]+公司[^\n]*)\s*\n([^\n]+?)\s*[-–至到]\s*([^\n]+)",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                exp = {
                    "company": match[0].strip() if "公司" in match[0] else match[2].strip(),
                    "position": match[1].strip(),
                    "duration": match[2].strip() if "公司" not in match[2] else match[1].strip(),
                    "description": "",
                }
                experiences.append(exp)

        return experiences[:5]  # 最多5段经历

    def _extract_summary(self, text: str) -> Optional[str]:
        """提取个人简介/求职意向"""
        # 匹配个人简介或自我评价
        patterns = [
            r"个\s*人\s*(?:简\s*介|评\s*价)[:：]?\s*([^\n]+(?:\n[^\n]+){0,3})",
            r"自\s*我\s*(?:介\s*绍|评\s*价)[:：]?\s*([^\n]+(?:\n[^\n]+){0,3})",
            r"求\s*职\s*意\s*向[:：]?\s*([^\n]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                summary = match.group(1).strip()
                if len(summary) > 10:
                    return summary[:500]  # 限制长度

        return None