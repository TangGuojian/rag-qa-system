"""一键启动脚本。

目标：让第一次接触本项目的人，在装完 Python 依赖后只跑这一条命令就能看到完整界面。
它依次完成：建库建表 → 建默认管理员 → （可选）导入示例文档 → 启动服务并打印访问地址。

用法：
    cd backend
    python run_demo.py                 # 启动服务
    python run_demo.py --import-demo   # 额外导入 demo_docs 下的示例文档（需要已配置 API Key）
    python run_demo.py --port 8080     # 指定端口

说明：示例文档的导入需要调用向量化接口，因此必须先有可用的 API Key。
没有 Key 时脚本会跳过这一步并给出提示，界面里上传文档即可。
"""

import argparse
import os
import sys
import webbrowser
from pathlib import Path

# 保证无论从哪个目录执行，都能正确导入 app 包并读取 backend/.env
BACKEND_DIR = Path(__file__).resolve().parent
os.chdir(BACKEND_DIR)
sys.path.insert(0, str(BACKEND_DIR))

DEMO_DOCS_DIR = BACKEND_DIR / "demo_docs"
DEFAULT_ADMIN = ("admin", "admin123")


def _line(char: str = "-", n: int = 62) -> str:
    return char * n


def step_prepare_database() -> None:
    from app.db.mysql import Base, engine
    from app.db.migrations import ensure_schema
    from app.core.config import settings

    # 必须先导入模型模块，否则 create_all 不知道要建哪些表
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    applied = ensure_schema(engine)
    if applied:
        print(f"  [数据库] 已补齐字段: {', '.join(applied)}")
    print(f"  [数据库] {engine.url.render_as_string(hide_password=True)}")
    if settings.is_sqlite:
        print("           使用内置 SQLite，无需安装任何数据库服务。")


def step_create_admin() -> "object":
    from app.db.mysql import SessionLocal
    from app.models.user import User, UserRole, UserStatus
    from app.core.auth import hash_password

    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == DEFAULT_ADMIN[0]).first()
        if admin:
            print(f"  [账号] 已存在：{DEFAULT_ADMIN[0]} / {DEFAULT_ADMIN[1]}")
            return admin
        admin = User(
            username=DEFAULT_ADMIN[0],
            password_hash=hash_password(DEFAULT_ADMIN[1]),
            display_name="系统管理员",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        print(f"  [账号] 已创建：{DEFAULT_ADMIN[0]} / {DEFAULT_ADMIN[1]}")
        return admin
    finally:
        db.close()


def step_import_demo(admin: "object") -> None:
    """把 demo_docs 下的示例文档灌进一个演示知识库。

    需要可用的 API Key（用户自己的或 .env 中的系统默认 Key）；没有则跳过。
    """
    from app.db.mysql import SessionLocal
    from app.models.kb import KnowledgeBase
    from app.models.document import Document, DocStatus, DocType
    from app.core.ai_config import AIConfig, for_user
    from app.api.documents import _parse_and_index

    if not DEMO_DOCS_DIR.is_dir():
        print("  [示例] 未找到 demo_docs 目录，跳过")
        return

    db = SessionLocal()
    try:
        ai: AIConfig = for_user(admin)
        if not ai.has_key:
            print("  [示例] 跳过：尚未配置 API Key，无法向量化文档。")
            print("         配置方法见启动后打印的提示，或查看 README。")
            return

        kb = db.query(KnowledgeBase).filter(KnowledgeBase.name == "示例知识库").first()
        if not kb:
            kb = KnowledgeBase(name="示例知识库", description="由 run_demo.py 自动创建的演示知识库")
            db.add(kb)
            db.commit()
            db.refresh(kb)

        imported = 0
        for path in sorted(DEMO_DOCS_DIR.iterdir()):
            if path.suffix.lower() not in {".txt", ".md"}:
                continue
            exists = (
                db.query(Document)
                .filter(Document.kb_id == kb.id, Document.filename == path.name)
                .first()
            )
            if exists and exists.status == DocStatus.COMPLETED:
                continue

            doc = exists or Document(
                kb_id=kb.id,
                filename=path.name,
                filepath=str(path),
                file_size=path.stat().st_size,
                file_type=DocType.TXT if path.suffix.lower() == ".txt" else DocType.MD,
                uploaded_by=admin.id,
            )
            if not exists:
                db.add(doc)
                db.commit()
                db.refresh(doc)

            try:
                _parse_and_index(doc, db, ai)
                print(f"  [示例] 已导入：{path.name}（{doc.chunk_count} 个片段）")
                imported += 1
            except Exception as exc:  # noqa: BLE001
                doc.status = DocStatus.FAILED
                doc.error_msg = str(exc)[:300]
                db.commit()
                print(f"  [示例] 导入失败：{path.name} -> {str(exc)[:120]}")

        print(f"  [示例] 导入完成，共 {imported} 篇，知识库：{kb.name}")
    finally:
        db.close()


def print_guide(port: int, has_frontend: bool) -> None:
    base = f"http://127.0.0.1:{port}"
    print(_line("="))
    print("  服务已启动")
    print(_line("="))
    if has_frontend:
        print(f"  打开界面：{base}")
    else:
        print(f"  接口文档：{base}/docs")
        print("  未找到前端构建产物 frontend/dist，界面未托管。")
        print("  可在 frontend/ 下执行 npm install && npm run build 后重启。")
    print(f"  默认账号：{DEFAULT_ADMIN[0]} / {DEFAULT_ADMIN[1]}")
    print(_line())
    print("  接下来三步：")
    print("    1. 用上面的账号登录")
    print("    2. 进入「个人设置」→ 选服务商 → 填自己的 API Key → 点「测试连接」")
    print("    3. 新建知识库 → 上传文档 → 开始提问")
    print()
    print("  没有 API Key？可查看 README 的「Key 从哪来」一节，")
    print("  阿里云百炼、硅基流动、智谱等都有免费额度。")
    print(_line("="))
    print("  按 Ctrl+C 停止服务")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="一键启动智能问答系统（零外部依赖）")
    parser.add_argument("--host", default="127.0.0.1", help="监听地址，默认 127.0.0.1")
    parser.add_argument("--port", type=int, default=8000, help="监听端口，默认 8000")
    parser.add_argument("--import-demo", action="store_true", help="启动时导入 demo_docs 下的示例文档")
    parser.add_argument("--no-browser", action="store_true", help="不自动打开浏览器")
    args = parser.parse_args()

    print(_line("="))
    print("  智能问答系统 · 一键启动")
    print(_line("="))

    try:
        step_prepare_database()
        admin = step_create_admin()
        if args.import_demo:
            step_import_demo(admin)
    except Exception as exc:  # noqa: BLE001
        print(f"\n初始化失败：{type(exc).__name__}: {exc}")
        print("请确认已安装依赖：pip install -r requirements.txt")
        sys.exit(1)

    has_frontend = (BACKEND_DIR.parent / "frontend" / "dist" / "index.html").is_file()
    print_guide(args.port, has_frontend)

    if has_frontend and not args.no_browser:
        try:
            webbrowser.open(f"http://127.0.0.1:{args.port}")
        except Exception:  # noqa: BLE001
            pass

    import uvicorn

    uvicorn.run("app.main:app", host=args.host, port=args.port, reload=False, log_level="info")


if __name__ == "__main__":
    main()
