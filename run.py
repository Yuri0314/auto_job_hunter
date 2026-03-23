#!/usr/bin/env python
"""
Auto Job Hunter - 自动求职投递系统

快速启动入口
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.cli import main

if __name__ == "__main__":
    main()