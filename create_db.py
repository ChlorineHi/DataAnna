import mysql.connector

# 连接到 MySQL 服务器
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="123456"
)

# 创建游标
cursor = conn.cursor()

# 创建数据库
cursor.execute("CREATE DATABASE IF NOT EXISTS dssec_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")

# 关闭连接
cursor.close()
conn.close()

print("数据库 dssec_db 创建成功！")
