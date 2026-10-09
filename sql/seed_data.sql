-- =========================================================================
-- IT Service Request Management System - MariaDB Seed Data
-- =========================================================================

USE it_service_db;

-- 1. Insert Users
INSERT INTO users (id, username, email, full_name, role, department, is_active, created_at) VALUES
(1, 'alex.chen', 'alex.chen@company.com', 'Alex Chen', 'IT_SUPPORT', 'IT Operations', 1, NOW()),
(2, 'sarah.jenkins', 'sarah.j@company.com', 'Sarah Jenkins', 'IT_SUPPORT', 'IT Operations', 1, NOW()),
(3, 'marcus.vance', 'marcus.v@company.com', 'Marcus Vance', 'IT_MANAGER', 'IT Management', 1, NOW()),
(4, 'admin.sys', 'admin@company.com', 'System Administrator', 'ADMIN', 'Infrastructure', 1, NOW()),
(5, 'emily.watson', 'emily.w@company.com', 'Emily Watson', 'EMPLOYEE', 'Finance', 1, NOW()),
(6, 'david.kim', 'david.k@company.com', 'David Kim', 'EMPLOYEE', 'Marketing', 1, NOW()),
(7, 'priya.sharma', 'priya.s@company.com', 'Priya Sharma', 'EMPLOYEE', 'Human Resources', 1, NOW()),
(8, 'jordan.lee', 'jordan.l@company.com', 'Jordan Lee', 'EMPLOYEE', 'Sales', 1, NOW())
ON DUPLICATE KEY UPDATE full_name=VALUES(full_name);

-- 2. Insert Categories
INSERT INTO categories (id, name, description, is_active, created_at) VALUES
(1, 'Hardware', 'Laptops, monitors, keyboards, docking stations, printers', 1, NOW()),
(2, 'Software', 'OS issues, standard software licenses, application bugs', 1, NOW()),
(3, 'Network', 'Wi-Fi connectivity, VPN access, LAN ports, bandwidth issues', 1, NOW()),
(4, 'Access / Permission', 'Shared drive access, database permissions, system logins', 1, NOW()),
(5, 'Email', 'Outlook, distribution lists, mailbox size, spam issues', 1, NOW()),
(6, 'Other', 'General technology requests and inquiries', 1, NOW())
ON DUPLICATE KEY UPDATE name=VALUES(name);

-- 3. Insert SLA Configurations
INSERT INTO sla_configs (id, priority, resolution_sla_hours, response_sla_hours, is_active, updated_at) VALUES
(1, 'CRITICAL', 4.0, 0.5, 1, NOW()),
(2, 'HIGH', 8.0, 1.0, 1, NOW()),
(3, 'MEDIUM', 24.0, 2.0, 1, NOW()),
(4, 'LOW', 48.0, 4.0, 1, NOW())
ON DUPLICATE KEY UPDATE resolution_sla_hours=VALUES(resolution_sla_hours);
