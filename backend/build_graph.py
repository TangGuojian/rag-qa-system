"""
从文档文件名中提取法规实体，构建 Neo4j 知识图谱
用法: python build_graph.py
"""
import os
import sys
import re
import time
import io

sys.path.insert(0, os.path.dirname(__file__))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from app.db.neo4j_db import neo4j_driver as driver

DOCUMENT_DIRS = [
    os.getenv("KB1_DATA_DIR", r"data\公司相关制度"),
    os.getenv("KB2_DATA_DIR", r"data\财政数据集\制度文件"),
]

# Regex patterns for extracting document info
PATTERN_DOCNUM = re.compile(r"([\u4e00-\u9fa5)]{2,8}(?:令|发|办|函)?(?:〔|\()?\d{4}(?:〕|\))?(?:\s*\d{1,4}号)?)")
PATTERN_AGENCY = re.compile(r"(\w+(?:省|市|自治区|自治州)?(?:人民政府|财政厅|财政部|办公厅|发改委|税务总局|应急部|国家\w+局|外交部|国管局|中直管理局|公务员局|中组部|国家档案局|人事部|工业和信息化部|中国人民银行|国家机关事务管理局|中共中央直属机关事务管理局))")
PATTERN_TITLE = re.compile(r"[《]([^》]+)[》]")


def extract_from_filename(filename: str) -> dict:
    name_no_ext = os.path.splitext(filename)[0]
    # Remove leading numbers like "00 ", "01 "
    name_no_ext = re.sub(r"^\d{2}\s+(新增|更新|替换)?\s*", "", name_no_ext)

    doc_num = ""
    agency = ""
    title = ""

    title_match = PATTERN_TITLE.search(filename)
    if title_match:
        title = title_match.group(1)

    agency_match = PATTERN_AGENCY.search(filename)
    if agency_match:
        agency = agency_match.group(1)

    doc_num_match = PATTERN_DOCNUM.search(name_no_ext)
    if doc_num_match:
        doc_num = doc_num_match.group(1)

    return {
        "doc_num": doc_num or name_no_ext.split(" ")[0],
        "agency": agency or "未知",
        "title": title or name_no_ext,
        "full_name": name_no_ext,
    }


def build_graph(close_driver: bool = True):
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
        print("Cleared existing graph data")

        for data_dir in DOCUMENT_DIRS:
            if not os.path.isdir(data_dir):
                print(f"Directory not found: {data_dir}")
                continue

            dir_name = os.path.basename(data_dir.rstrip("\\"))
            session.run(
                "MERGE (:Category {name: $name})",
                name=dir_name,
            )

            for fname in os.listdir(data_dir):
                ext = os.path.splitext(fname)[1].lower()
                if ext not in (".md", ".pdf"):
                    continue

                info = extract_from_filename(fname)

                session.run("""
                    MERGE (d:Document {name: $full_name, filename: $filename})
                    SET d.doc_num = $doc_num, d.title = $title
                """, **info, filename=fname)

                if info["agency"] != "未知":
                    session.run("""
                        MERGE (a:Agency {name: $agency})
                        MERGE (d:Document {name: $full_name})
                        MERGE (a)-[:PUBLISHED]->(d)
                    """, **info)

                if info["doc_num"]:
                    session.run("""
                        MERGE (n:DocNumber {number: $doc_num})
                        MERGE (d:Document {name: $full_name})
                        MERGE (d)-[:HAS_NUMBER]->(n)
                    """, **info)

                session.run("""
                    MATCH (cat:Category {name: $cat_name})
                    MERGE (d:Document {name: $full_name})
                    MERGE (d)-[:BELONGS_TO]->(cat)
                """, cat_name=dir_name, **info)

                print(f"  + {fname}")

        # Build statistics
        result = session.run("""
            MATCH (n) RETURN labels(n)[0] AS label, count(*) AS cnt
            ORDER BY cnt DESC
        """)
        print("\nGraph statistics:")
        for record in result:
            print(f"  {record['label']}: {record['cnt']}")

    if close_driver:
        driver.close()
    print("\nGraph build completed!")


if __name__ == "__main__":
    start = time.time()
    build_graph()
    elapsed = time.time() - start
    print(f"Time: {elapsed:.1f}s")
