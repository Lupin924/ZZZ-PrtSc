#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
截图工具入口
基于CustomTkinter + BitBlt + Windows API
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.main import main

if __name__ == "__main__":
    main()
