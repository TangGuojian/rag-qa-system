import traceback
from fastapi import APIRouter, Depends, HTTPException
from app.db.neo4j_db import neo4j_driver
from app.core.dependencies import get_current_user, require_admin
from app.models.user import User
from build_graph import build_graph as run_build

router = APIRouter()


@router.get("/data")
def get_graph_data(user: User = Depends(get_current_user)):
    nodes = []
    edges = []
    node_ids = set()

    try:
        with neo4j_driver.session() as session:
            for record in session.run("MATCH (n) RETURN id(n) AS id, labels(n) AS labels, n.name AS name, n.title AS title, n.doc_num AS doc_num"):
                nid = record["id"]
                if nid in node_ids:
                    continue
                node_ids.add(nid)
                label = record["labels"][0] if record["labels"] else "Unknown"
                nodes.append({
                    "id": nid,
                    "label": label,
                    "name": record["name"] or record["title"] or "",
                    "doc_num": record["doc_num"] or "",
                })

            for record in session.run("""
                MATCH (a)-[r]->(b)
                RETURN id(a) AS source, id(b) AS target, type(r) AS label
            """):
                edges.append({
                    "source": record["source"],
                    "target": record["target"],
                    "label": record["label"],
                })
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Neo4j 连接失败: {str(e)}")

    return {"nodes": nodes, "edges": edges}


@router.post("/build")
def build_graph_endpoint(user: User = Depends(require_admin)):
    try:
        run_build(close_driver=False)
        return {"message": "图谱构建完成"}
    except Exception as e:
        err = str(e)
        if "connect" in err.lower() or "refused" in err.lower():
            detail = "Neo4j 数据库未运行，请先启动 Neo4j 服务"
        else:
            detail = f"图谱构建失败: {err}"
        raise HTTPException(status_code=503, detail=detail)
