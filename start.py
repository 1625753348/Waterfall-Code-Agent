#!/usr/bin/env python3
"""Waterfall Agent - SDLC 自动化系统 启动脚本"""

import sys
import os
import webbrowser
from threading import Timer

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "127.0.0.1")

    print("=" * 60)
    print("  Waterfall Agent - SDLC 自动化系统")
    print("  8阶段瀑布式软件工程Agent")
    print("=" * 60)
    print(f"\n  Web UI: http://{host}:{port}")
    print(f"  API:    http://{host}:{port}/api/health")
    print("\n  按 Ctrl+C 停止服务\n")

    def open_browser():
        webbrowser.open(f"http://{host}:{port}")

    Timer(1.5, open_browser).start()

    uvicorn.run(
        "backend.main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info",
    )
