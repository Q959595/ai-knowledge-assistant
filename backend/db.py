"""数据库工具层：基于 pymysql 的轻量封装。

设计要点：
  - 所有 SQL 全部使用参数化查询（%s 占位符），避免 SQL 注入；
  - 提供 query（查询）和 execute（增删改）两个函数，业务代码里直接调用；
  - 每次操作独立连接、用后即关，简单可靠，适合中小项目。
"""
import pymysql

from config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME


def get_conn():
    """获取一个新的数据库连接；结果以字典（dict）返回，方便按列名取值。"""
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,  # 关闭自动提交，由 execute 手动控制事务
    )


def query(sql, args=None, one=False):
    """执行 SELECT 查询。

    one=True 时只返回第一条记录（dict 或 None），否则返回 list[dict]。
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, args or ())
            rows = cur.fetchall()
        return (rows[0] if rows else None) if one else rows
    finally:
        conn.close()


def execute(sql, args=None):
    """执行 INSERT / UPDATE / DELETE。

    返回：
      - INSERT 时返回新记录的自增主键 id；
      - 其他语句返回影响的行数。
    出错时回滚事务并重新抛出异常。
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, args or ())
            conn.commit()  # 提交事务
            return cur.lastrowid
    except Exception:
        conn.rollback()  # 出错回滚，保证数据一致
        raise
    finally:
        conn.close()
