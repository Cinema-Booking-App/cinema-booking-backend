INSERT INTO roles (role_name, description) VALUES
('super_admin', 'Người quản trị hệ thống cao nhất'),
('cinema_manager', 'Người quản lý rạp chiếu phim'),
('counter_staff', 'Nhân viên bán vé tại quầy'),
('user', 'Người dùng thông thường, khách hàng'); -- Đây là vai trò mặc định

INSERT INTO roles (role_name, description) VALUES
('general_manager', 'Admin tổng'),
('cinema_manager', 'Quản lý rạp'),
('counter_staff', 'Quản lý quầy');

INSERT INTO permissions (permission_name, description) VALUES
('access:admin', 'Truy cập trang admin'),
('manage:dashboard', 'Xem dashboard'),
('manage:cinemas', 'Quản lý rạp'),
('manage:rooms', 'Quản lý phòng chiếu'),
('manage:seats', 'Quản lý ghế'),
('manage:schedules', 'Quản lý lịch chiếu'),
('manage:movies', 'Quản lý phim'),
('manage:bookings', 'Quản lý vé'),
('manage:combos', 'Quản lý combo'),
('manage:customers', 'Quản lý khách hàng'),
('manage:staff', 'Quản lý nhân viên'),
('manage:promotions', 'Quản lý khuyến mãi'),
('manage:reports', 'Quản lý báo cáo'),
('manage:content', 'Quản lý nội dung'),
('manage:maintenance', 'Bảo trì hệ thống'),
('manage:permissions', 'Quản lý phân quyền'),
('manage:support', 'Hỗ trợ khách hàng'),
('manage:settings', 'Cài đặt hệ thống'),
('manage:members', 'Quản lý thành viên');

-- general_manager: Tất cả quyền
INSERT INTO role_permissions (role_id, permission_id)
SELECT (SELECT role_id FROM roles WHERE role_name = 'general_manager'), permission_id
FROM permissions;

-- cinema_manager: Quyền liên quan đến rạp
INSERT INTO role_permissions (role_id, permission_id) VALUES
((SELECT role_id FROM roles WHERE role_name = 'cinema_manager'),
 (SELECT permission_id FROM permissions WHERE permission_name = 'access:admin')),
((SELECT role_id FROM roles WHERE role_name = 'cinema_manager'),
 (SELECT permission_id FROM permissions WHERE permission_name = 'manage:dashboard')),
((SELECT role_id FROM roles WHERE role_name = 'cinema_manager'),
 (SELECT permission_id FROM permissions WHERE permission_name = 'manage:cinemas')),
((SELECT role_id FROM roles WHERE role_name = 'cinema_manager'),
 (SELECT permission_id FROM permissions WHERE permission_name = 'manage:rooms')),
((SELECT role_id FROM roles WHERE role_name = 'cinema_manager'),
 (SELECT permission_id FROM permissions WHERE permission_name = 'manage:seats')),
((SELECT role_id FROM roles WHERE role_name = 'cinema_manager'),
 (SELECT permission_id FROM permissions WHERE permission_name = 'manage:schedules')),
((SELECT role_id FROM roles WHERE role_name = 'cinema_manager'),
 (SELECT permission_id FROM permissions WHERE permission_name = 'manage:movies'));

-- counter_staff: Quyền liên quan đến vé và combo
INSERT INTO role_permissions (role_id, permission_id) VALUES
((SELECT role_id FROM roles WHERE role_name = 'counter_staff'),
 (SELECT permission_id FROM permissions WHERE permission_name = 'access:admin')),
((SELECT role_id FROM roles WHERE role_name = 'counter_staff'),
 (SELECT permission_id FROM permissions WHERE permission_name = 'manage:dashboard')),
((SELECT role_id FROM roles WHERE role_name = 'counter_staff'),
 (SELECT permission_id FROM permissions WHERE permission_name = 'manage:bookings')),
((SELECT role_id FROM roles WHERE role_name = 'counter_staff'),
 (SELECT permission_id FROM permissions WHERE permission_name = 'manage:combos'));

INSERT INTO user_roles (user_id, role_id) VALUES
((SELECT user_id FROM users WHERE full_name = 'super_admin_user'),
 (SELECT role_id FROM roles WHERE role_name = 'general_manager')),
((SELECT user_id FROM users WHERE full_name = 'cinema_manager_user'),
 (SELECT role_id FROM roles WHERE role_name = 'cinema_manager')),
((SELECT user_id FROM users WHERE full_name = 'counter_staff_user'),
 (SELECT role_id FROM roles WHERE role_name = 'counter_staff'));

INSERT INTO theaters (name, address, city, phone) VALUES
('CGV Vincom Center', '72 Lê Thánh Tôn, Bến Nghé, Quận 1', 'TP. Hồ Chí Minh', '02838222718'),
('Lotte Cinema Gò Vấp', '242 Nguyễn Văn Lượng, Phường 10, Gò Vấp', 'TP. Hồ Chí Minh', '02839841000'),
('BHD Star Bitexco', '2 Hải Triều, Bến Nghé, Quận 1', 'TP. Hồ Chí Minh', '02862620246');

INSERT INTO movies (title, genre, duration, age_rating, description, release_date, trailer_url, poster_url, status, director, actors) VALUES
('Minions: Sự Trỗi Dậy Của Gru', 'Hoạt hình, Hài, Phiêu lưu', 90, 'P', 'Câu chuyện về Gru thời trẻ và những Minions của mình.', '2022-07-01', 'https://www.youtube.com/watch?v=0', 'https://example.com/minions_poster.jpg', 'now_showing', 'Kyle Balda', 'Steve Carell, Pierre Coffin'),
('Top Gun: Maverick', 'Hành động, Phiêu lưu', 130, 'C13', 'Pete "Maverick" Mitchell đối mặt với quá khứ của mình.', '2022-05-27', 'https://www.youtube.com/watch?v=1', 'https://example.com/topgun_poster.jpg', 'now_showing', 'Joseph Kosinski', 'Tom Cruise, Miles Teller'),
('Black Panther: Wakanda Forever', 'Hành động, Phiêu lưu, Khoa học viễn tưởng', 161, 'C13', 'Nữ hoàng Ramonda, Shuri, M’Baku, Okoye và Dora Milaje đấu tranh để bảo vệ quốc gia của mình.', '2022-11-11', 'https://www.youtube.com/watch?v=2', 'https://example.com/blackpanther_poster.jpg', 'upcoming', 'Ryan Coogler', 'Letitia Wright, Lupita Nyong''o'),
('Avatar: Dòng Chảy Của Nước', 'Khoa học viễn tưởng, Hành động, Phiêu lưu', 192, 'C13', 'Câu chuyện về gia đình Sully, những nỗ lực của họ để giữ an toàn cho nhau, những trận chiến mà họ phải chiến đấu để tồn tại.', '2022-12-16', 'https://www.youtube.com/watch?v=3', 'https://example.com/avatar_poster.jpg', 'upcoming', 'James Cameron', 'Sam Worthington, Zoe Saldaña');

INSERT INTO seat_layouts (layout_name, total_rows, total_columns, aisle_positions) VALUES
('Layout A (Standard)', 5, 10, '[{"row": 3, "col": 5}, {"row": 3, "col": 6}]'),
('Layout B (Small Room)', 4, 8, '[]');

INSERT INTO seat_templates (layout_id, row_number, column_number, seat_code, seat_type, is_edge, is_active) VALUES
((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout A (Standard)'), 1, 1, 'A1', 'regular', TRUE, TRUE),
((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout A (Standard)'), 1, 2, 'A2', 'regular', FALSE, TRUE),
((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout A (Standard)'), 1, 3, 'A3', 'regular', FALSE, TRUE),
((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout A (Standard)'), 1, 4, 'A4', 'regular', FALSE, TRUE),
((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout A (Standard)'), 1, 5, 'A5', 'regular', FALSE, TRUE),
((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout A (Standard)'), 1, 6, 'A6', 'regular', FALSE, TRUE),
((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout A (Standard)'), 1, 7, 'A7', 'regular', FALSE, TRUE),
((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout A (Standard)'), 1, 8, 'A8', 'regular', FALSE, TRUE),
((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout A (Standard)'), 1, 9, 'A9', 'regular', FALSE, TRUE),
((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout A (Standard)'), 1, 10, 'A10', 'regular', TRUE, TRUE),
((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout A (Standard)'), 2, 1, 'B1', 'regular', TRUE, TRUE),
((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout A (Standard)'), 2, 2, 'B2', 'regular', FALSE, TRUE),
((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout A (Standard)'), 2, 3, 'B3', 'regular', FALSE, TRUE),
((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout A (Standard)'), 2, 4, 'B4', 'regular', FALSE, TRUE),
((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout A (Standard)'), 2, 5, 'B5', 'regular', FALSE, TRUE),
((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout A (Standard)'), 2, 6, 'B6', 'regular', FALSE, TRUE),
((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout A (Standard)'), 2, 7, 'B7', 'regular', FALSE, TRUE),
((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout A (Standard)'), 2, 8, 'B8', 'regular', FALSE, TRUE),
((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout A (Standard)'), 2, 9, 'B9', 'regular', FALSE, TRUE),
((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout A (Standard)'), 2, 10, 'B10', 'regular', TRUE, TRUE),
((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout A (Standard)'), 3, 1, 'C1', 'regular', TRUE, TRUE),
((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout A (Standard)'), 3, 2, 'C2', 'regular', FALSE, TRUE),
((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout A (Standard)'), 3, 3, 'C3', 'vip', FALSE, TRUE),
((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout A (Standard)'), 3, 4, 'C4', 'vip', FALSE, TRUE),
((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout A (Standard)'), 3, 5, 'C5', 'vip', FALSE, TRUE),
((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout A (Standard)'), 3, 6, 'C6', 'vip', FALSE, TRUE),
((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout A (Standard)'), 3, 7, 'C7', 'vip', FALSE, TRUE),
((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout A (Standard)'), 3, 8, 'C8', 'regular', FALSE, TRUE),
((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout A (Standard)'), 3, 9, 'C9', 'regular', FALSE, TRUE),
((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout A (Standard)'), 3, 10, 'C10', 'regular', TRUE, TRUE),
((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout A (Standard)'), 4, 1, 'D1', 'regular', TRUE, TRUE),
((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout A (Standard)'), 4, 2, 'D2', 'regular', FALSE, TRUE),
((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout A (Standard)'), 4, 3, 'D3', 'regular', FALSE, TRUE),
((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout A (Standard)'), 4, 4, 'D4', 'regular', FALSE, TRUE),
((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout A (Standard)'), 4, 5, 'D5', 'regular', FALSE, TRUE),
((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout A (Standard)'), 4, 6, 'D6', 'regular', FALSE, TRUE),
((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout A (Standard)'), 4, 7, 'D7', 'regular', FALSE, TRUE),
((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout A (Standard)'), 4, 8, 'D8', 'regular', FALSE, TRUE),
((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout A (Standard)'), 4, 9, 'D9', 'regular', FALSE, TRUE),
((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout A (Standard)'), 4, 10, 'D10', 'regular', TRUE, TRUE),
((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout A (Standard)'), 5, 1, 'E1', 'regular', TRUE, TRUE),
((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout A (Standard)'), 5, 2, 'E2', 'regular', FALSE, TRUE),
((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout A (Standard)'), 5, 3, 'E3', 'couple', FALSE, TRUE),
((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout A (Standard)'), 5, 4, 'E4', 'couple', FALSE, TRUE),
((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout A (Standard)'), 5, 5, 'E5', 'couple', FALSE, TRUE),
((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout A (Standard)'), 5, 6, 'E6', 'couple', FALSE, TRUE),
((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout A (Standard)'), 5, 7, 'E7', 'couple', FALSE, TRUE),
((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout A (Standard)'), 5, 8, 'E8', 'regular', FALSE, TRUE),
((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout A (Standard)'), 5, 9, 'E9', 'regular', FALSE, TRUE),
((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout A (Standard)'), 5, 10, 'E10', 'regular', TRUE, TRUE),
((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout B (Small Room)'), 1, 1, 'A1', 'regular', TRUE, TRUE), ((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout B (Small Room)'), 1, 2, 'A2', 'regular', FALSE, TRUE), ((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout B (Small Room)'), 1, 3, 'A3', 'regular', FALSE, TRUE), ((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout B (Small Room)'), 1, 4, 'A4', 'regular', FALSE, TRUE), ((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout B (Small Room)'), 1, 5, 'A5', 'regular', FALSE, TRUE), ((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout B (Small Room)'), 1, 6, 'A6', 'regular', FALSE, TRUE), ((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout B (Small Room)'), 1, 7, 'A7', 'regular', FALSE, TRUE), ((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout B (Small Room)'), 1, 8, 'A8', 'regular', TRUE, TRUE),
((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout B (Small Room)'), 2, 1, 'B1', 'regular', TRUE, TRUE), ((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout B (Small Room)'), 2, 2, 'B2', 'regular', FALSE, TRUE), ((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout B (Small Room)'), 2, 3, 'B3', 'regular', FALSE, TRUE), ((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout B (Small Room)'), 2, 4, 'B4', 'regular', FALSE, TRUE), ((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout B (Small Room)'), 2, 5, 'B5', 'regular', FALSE, TRUE), ((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout B (Small Room)'), 2, 6, 'B6', 'regular', FALSE, TRUE), ((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout B (Small Room)'), 2, 7, 'B7', 'regular', FALSE, TRUE), ((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout B (Small Room)'), 2, 8, 'B8', 'regular', TRUE, TRUE),
((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout B (Small Room)'), 3, 1, 'C1', 'regular', TRUE, TRUE), ((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout B (Small Room)'), 3, 2, 'C2', 'regular', FALSE, TRUE), ((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout B (Small Room)'), 3, 3, 'C3', 'regular', FALSE, TRUE), ((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout B (Small Room)'), 3, 4, 'C4', 'regular', FALSE, TRUE), ((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout B (Small Room)'), 3, 5, 'C5', 'regular', FALSE, TRUE), ((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout B (Small Room)'), 3, 6, 'C6', 'regular', FALSE, TRUE), ((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout B (Small Room)'), 3, 7, 'C7', 'regular', FALSE, TRUE), ((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout B (Small Room)'), 3, 8, 'C8', 'regular', TRUE, TRUE),
((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout B (Small Room)'), 4, 1, 'D1', 'regular', TRUE, TRUE), ((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout B (Small Room)'), 4, 2, 'D2', 'regular', FALSE, TRUE), ((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout B (Small Room)'), 4, 3, 'D3', 'regular', FALSE, TRUE), ((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout B (Small Room)'), 4, 4, 'D4', 'regular', FALSE, TRUE), ((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout B (Small Room)'), 4, 5, 'D5', 'regular', FALSE, TRUE), ((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout B (Small Room)'), 4, 6, 'D6', 'regular', FALSE, TRUE), ((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout B (Small Room)'), 4, 7, 'D7', 'regular', FALSE, TRUE), ((SELECT layout_id FROM seat_layouts WHERE layout_name = 'Layout B (Small Room)'), 4, 8, 'D8', 'regular', TRUE, TRUE);