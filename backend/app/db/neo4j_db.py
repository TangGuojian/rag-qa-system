from neo4j import GraphDatabase
from app.core.config import settings

neo4j_driver = GraphDatabase.driver(
    settings.neo4j_uri,
    auth=(settings.neo4j_user, settings.neo4j_password),
)


def get_neo4j_session():
    with neo4j_driver.session() as session:
        yield session


def close_neo4j():
    neo4j_driver.close()
