# Servicio para métricas y dashboard
import os
import psycopg2
from datetime import datetime, timedelta

DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "feedback975")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "postgres")


def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )


def get_total_interactions():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM interactions;")
            return cur.fetchone()[0]


def get_avg_synthesis_feedback():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT AVG(synthesis_feedback) FROM interactions WHERE synthesis_feedback IS NOT NULL;")
            return float(cur.fetchone()[0] or 0)


def get_avg_graph_feedback():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT AVG(graph_feedback) FROM interactions WHERE graph_feedback IS NOT NULL;")
            return float(cur.fetchone()[0] or 0)


def get_feedback_type_distribution():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT feedback_type, COUNT(*) FROM interactions GROUP BY feedback_type;")
            return dict(cur.fetchall())


def get_client_version_distribution():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT client_version, COUNT(*) FROM interactions GROUP BY client_version;")
            return dict(cur.fetchall())


def get_interactions_last_30_days():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT to_char(timestamp, 'YYYY-MM-DD') as day, COUNT(*)
                FROM interactions
                WHERE timestamp >= %s
                GROUP BY day
                ORDER BY day ASC;
            """, (datetime.now() - timedelta(days=30),))
            return cur.fetchall()


def get_feedback_split():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT has_feedback, COUNT(*) FROM interactions GROUP BY has_feedback;")
            # Devuelve {'true': n, 'false': m}
            rows = cur.fetchall()
            return {str(r[0]).lower(): r[1] for r in rows}


def get_synthesis_feedback_histogram():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT synthesis_feedback, COUNT(*)
                FROM interactions
                WHERE synthesis_feedback IS NOT NULL
                GROUP BY synthesis_feedback
                ORDER BY synthesis_feedback
            """)
            return {int(r[0]): r[1] for r in cur.fetchall() if r[0] is not None}


def get_graph_feedback_histogram():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT graph_feedback, COUNT(*)
                FROM interactions
                WHERE graph_feedback IS NOT NULL
                GROUP BY graph_feedback
                ORDER BY graph_feedback
            """)
            return {int(r[0]): r[1] for r in cur.fetchall() if r[0] is not None}


def get_avg_synthesis_feedback_by_day():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT to_char(timestamp, 'YYYY-MM-DD') as day, AVG(synthesis_feedback)
                FROM interactions
                WHERE synthesis_feedback IS NOT NULL AND timestamp >= %s
                GROUP BY day
                ORDER BY day ASC;
            """, (datetime.now() - timedelta(days=30),))
            return [{"date": r[0], "avg": float(r[1])} for r in cur.fetchall()]


def get_avg_graph_feedback_by_day():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT to_char(timestamp, 'YYYY-MM-DD') as day, AVG(graph_feedback)
                FROM interactions
                WHERE graph_feedback IS NOT NULL AND timestamp >= %s
                GROUP BY day
                ORDER BY day ASC;
            """, (datetime.now() - timedelta(days=30),))
            return [{"date": r[0], "avg": float(r[1])} for r in cur.fetchall()]


def get_top_collections(limit=10):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT relevance_filtered_collections, COUNT(*) as c
                FROM interactions
                WHERE relevance_filtered_collections IS NOT NULL AND relevance_filtered_collections != ''
                GROUP BY relevance_filtered_collections
                ORDER BY c DESC
                LIMIT %s;
            """, (limit,))
            return [{"collection": r[0], "count": r[1]} for r in cur.fetchall()]


def get_dashboard_metrics():
    return {
        "total_interactions": get_total_interactions(),
        "avg_synthesis_feedback": get_avg_synthesis_feedback(),
        "avg_graph_feedback": get_avg_graph_feedback(),
        "feedback_type_distribution": get_feedback_type_distribution(),
        "client_version_distribution": get_client_version_distribution(),
        "interactions_last_30_days": get_interactions_last_30_days(),
        "feedback_split": get_feedback_split(),
        "synthesis_feedback_histogram": get_synthesis_feedback_histogram(),
        "graph_feedback_histogram": get_graph_feedback_histogram(),
        "avg_synthesis_feedback_by_day": get_avg_synthesis_feedback_by_day(),
        "avg_graph_feedback_by_day": get_avg_graph_feedback_by_day(),
        "top_collections": get_top_collections(),
    }