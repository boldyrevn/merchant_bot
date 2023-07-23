"""
admin information added
"""

from yoyo import step

__depends__ = {'20230708_01_JfNrB-create-database'}

steps = [
    step(f"ALTER TABLE merchants ADD COLUMN admin_username VARCHAR(64) DEFAULT 'Unknown'",
         f"ALTER TABLE merchants DROP COLUMN admin_username"),
    step(f"ALTER TABLE traders ADD COLUMN admin_username VARCHAR(64) DEFAULT 'Unknown'",
         f"ALTER TABLE traders DROP COLUMN admin_username")
]
