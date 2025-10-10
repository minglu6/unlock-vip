-- 数据库初始化脚本
-- 此脚本会在 MySQL 容器首次启动时自动执行

-- 设置字符集
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS unlock_vip CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE unlock_vip;

-- 注意：表结构会由 SQLAlchemy 自动创建
-- 这里只是预留脚本，可以添加初始数据

-- 示例：创建默认 API Key（可选）
-- 生产环境建议通过 manage_db.py 创建
