-- ============================================================
-- 基于多模型融合的心脏病风险预测系统 —— MySQL 初始化脚本
-- 执行方式：mysql -u root -p < sql/init.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS heart_disease_prediction DEFAULT CHARSET utf8mb4;
USE heart_disease_prediction;

-- 患者信息表
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL COMMENT '患者姓名',
    age INT COMMENT '年龄',
    gender VARCHAR(50) COMMENT '性别',
    symptoms TEXT COMMENT '症状',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    deleted_at TIMESTAMP NULL COMMENT '删除时间'
) COMMENT '患者管理表';

-- 管理员（登录）表：默认账号 admin / 123456，部署时请务必修改密码
CREATE TABLE IF NOT EXISTS manager (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL
) COMMENT '管理员登录表';

INSERT INTO manager (username, password) VALUES ('admin', '123456');

-- 诊断意见反馈表
CREATE TABLE IF NOT EXISTS diagnosis (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_name VARCHAR(255) NOT NULL COMMENT '患者姓名',
    feedback TEXT NOT NULL COMMENT '诊断意见',
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '提交时间'
) COMMENT '诊断意见反馈表';
