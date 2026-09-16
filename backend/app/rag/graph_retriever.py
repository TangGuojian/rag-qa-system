from app.db.neo4j_db import neo4j_driver
from app.utils.text import extract_chinese_words


class GraphResult:
    def __init__(self, content: str, source: str, score: float):
        self.content = content
        self.source = source
        self.score = score


def search_graph(question: str) -> list[GraphResult]:
    results = []

    with neo4j_driver.session() as session:
        for keyword in extract_chinese_words(question):
            for record in session.run("""
                MATCH (d:Document)
                WHERE d.full_name CONTAINS $keyword OR d.title CONTAINS $keyword
                RETURN d.full_name AS name, d.title AS title, d.filename AS filename
                LIMIT 5
            """, keyword=keyword):
                results.append(GraphResult(
                    content=f"法规名称: {record['title'] or record['name']}",
                    source=f"知识图谱(法规:{record['filename']})",
                    score=0.85,
                ))

            for record in session.run("""
                MATCH (a:Agency)-[:PUBLISHED]->(d:Document)
                WHERE a.name CONTAINS $keyword
                RETURN d.full_name AS name, a.name AS agency
                LIMIT 5
            """, keyword=keyword):
                results.append(GraphResult(
                    content=f"发文单位 {record['agency']} 发布的法规: {record['name']}",
                    source="知识图谱(发文单位)",
                    score=0.8,
                ))

    return results
