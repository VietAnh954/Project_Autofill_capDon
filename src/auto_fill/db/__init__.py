"""Database layer — SQLAlchemy models + engine factory.

Tầng DB nằm giữa pipeline và file tổng Excel:
  pipeline → db.repository → SQLite → daily export → Excel
"""
