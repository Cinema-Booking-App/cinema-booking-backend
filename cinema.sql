-- Phần 1: Tạo các kiểu dữ liệu ENUM
-- Các câu lệnh này sẽ gây lỗi nếu kiểu ENUM đã tồn tại.

CREATE TYPE age_rating_type AS ENUM ('P', 'C13', 'C16', 'C18');

CREATE TYPE movie_status_type AS ENUM ('upcoming', 'now_showing', 'ended');

CREATE TYPE seat_type AS ENUM ('regular', 'vip', 'couple');

CREATE TYPE ticket_status AS ENUM ('pending', 'confirmed', 'cancelled');

CREATE TYPE transaction_status AS ENUM ('pending', 'success', 'failed');

CREATE TYPE user_status AS ENUM ('pending', 'active', 'inactive');

CREATE TYPE combo_status AS ENUM ('active', 'inactive');

CREATE TYPE theater_type_status AS ENUM ('active', 'inactive');

CREATE TYPE showtimes_status AS ENUM ('active', 'inactive', 'sold_out');

CREATE TYPE language_type AS ENUM ('sub_vi', 'sub_en', 'dub_en', 'dub_vi', 'original');

CREATE TYPE format_type AS ENUM ('TWO_D', 'THREE_D', 'IMAX', '4DX');

-- Phần 2: Tạo các Bảng

-- Bảng Roles
CREATE TABLE roles (
    "role_id" SERIAL PRIMARY KEY,
    "role_name" VARCHAR(255) NOT NULL,
    "description" VARCHAR(255) UNIQUE NOT NULL
);

CREATE TABLE permissions (
    permission_id SERIAL PRIMARY KEY,
    permission_name VARCHAR(255) UNIQUE NOT NULL, -- Tên quyền (ví dụ: view_movies, create_showtimes)
    description TEXT NOT NULL, -- Mô tả quyền
    created_at TIMESTAMP
    WITH
        TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE role_permissions (
    role_id INTEGER NOT NULL,
    permission_id INTEGER NOT NULL,
    PRIMARY KEY (role_id, permission_id),
    FOREIGN KEY (role_id) REFERENCES roles (role_id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions (permission_id) ON DELETE CASCADE
);
-- Bảng Users
CREATE TABLE users (
    "user_id" SERIAL PRIMARY KEY,
    "full_name" VARCHAR(255) NOT NULL,
    "email" VARCHAR(255) UNIQUE NOT NULL,
    "password_hash" VARCHAR(255) NOT NULL,
    "status" user_status DEFAULT 'active',
    "created_at" TIMESTAMP
    WITH
        TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        "updated_at" TIMESTAMP
    WITH
        TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_roles (
    user_role_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    assigned_at TIMESTAMP
    WITH
        TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
        FOREIGN KEY (role_id) REFERENCES roles (role_id) ON DELETE CASCADE,
        UNIQUE (user_id, role_id)
);

-- Bảng Theaters (Rạp chiếu phim)
CREATE TABLE theaters (
    "theater_id" SERIAL PRIMARY KEY,
    "name" VARCHAR(255) UNIQUE NOT NULL,
    "address" TEXT NOT NULL,
    "city" VARCHAR(100),
    "phone" VARCHAR(20),
    "created_at" TIMESTAMP
    WITH
        TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Bảng Movies (Phim)
CREATE TABLE movies (
    "movie_id" SERIAL PRIMARY KEY,
    "title" VARCHAR(255) NOT NULL,
    "genre" VARCHAR(100),
    "duration" INTEGER NOT NULL,
    "age_rating" age_rating_type NOT NULL,
    "description" TEXT,
    "release_date" DATE,
    "trailer_url" VARCHAR(255),
    "poster_url" VARCHAR(255),
    "status" movie_status_type DEFAULT 'upcoming',
    "director" VARCHAR(255),
    "actors" TEXT,
    "created_at" TIMESTAMP
    WITH
        TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Bảng Promotions (Khuyến mãi)
CREATE TABLE promotions (
    "promotion_id" SERIAL PRIMARY KEY,
    "code" VARCHAR(50) UNIQUE NOT NULL,
    "discount_percentage" NUMERIC(5, 2),
    "start_date" DATE NOT NULL,
    "end_date" DATE NOT NULL,
    "max_usage" INTEGER,
    "used_count" INTEGER DEFAULT 0,
    "description" TEXT,
    "created_at" TIMESTAMP
    WITH
        TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Bảng Combos
CREATE TABLE combos (
    "combo_id" SERIAL PRIMARY KEY,
    "combo_name" VARCHAR(255) UNIQUE NOT NULL,
    "description" TEXT,
    "price" NUMERIC(10, 2) NOT NULL,
    "image_url" VARCHAR(255),
    "status" combo_status DEFAULT 'active',
);

-- Bảng ComboItems (Chi tiết các thành phần trong Combo)
CREATE TABLE combo_items (
    "item_id" SERIAL PRIMARY KEY,
    "combo_id" INTEGER NOT NULL,
    "dish_id" INTEGER NOT NULL,
    "quantity" INTEGER NOT NULL
);

-- Bảng ComboDishes (Chi tiết các thành phần trong Combo)
CREATE TABLE combo_dishes (
    "dish_id" SERIAL PRIMARY KEY,
    "dish_name" VARCHAR NOT NULL,
    "description" TEXT
);

-- Bảng Ranks
CREATE TABLE ranks (
    "rank_id" SERIAL PRIMARY KEY,              -- ID tự tăng
    "rank_name" VARCHAR(50) NOT NULL,           -- Tên cấp bậc
    "spending_target" NUMERIC(15,2) NOT NULL,   -- Tổng chi tiêu yêu cầu (VND)
    "ticket_percent" NUMERIC(5,2) NOT NULL,     -- % tích lũy khi mua vé
    "combo_percent" NUMERIC(5,2) NOT NULL,      -- % tích lũy khi mua combo
    "is_default" BOOLEAN DEFAULT FALSE,         -- Cấp mặc định hay không
    "created_at" TIMESTAMPTZ DEFAULT NOW(),     -- Ngày tạo
    "updated_at" TIMESTAMPTZ DEFAULT NOW() 
);

-- Bảng SeatLayouts (Bố cục ghế)
CREATE TABLE seat_layouts (
    "layout_id" SERIAL PRIMARY KEY,
    "layout_name" VARCHAR(100) UNIQUE NOT NULL,
    "description" TEXT,
    "total_rows" INTEGER NOT NULL,
    "total_columns" INTEGER NOT NULL,
    "aisle_positions" TEXT, -- Lưu dưới dạng JSON string
    "created_at" TIMESTAMP
    WITH
        TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Bảng SeatTemplates (Mẫu ghế cho bố cục)
CREATE TABLE seat_templates (
    "template_id" SERIAL PRIMARY KEY,
    "layout_id" INTEGER NOT NULL,
    "row_number" INTEGER NOT NULL,
    "column_number" INTEGER NOT NULL,
    "seat_code" VARCHAR(10) NOT NULL,
    "seat_type" seat_type DEFAULT 'regular',
    "is_edge" BOOLEAN DEFAULT FALSE,
    "is_active" BOOLEAN DEFAULT TRUE,
    "created_at" TIMESTAMP
    WITH
        TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        UNIQUE ("layout_id", "seat_code") -- Đảm bảo mã ghế duy nhất trong một bố cục
);

-- Bảng Rooms (Phòng chiếu)
CREATE TABLE rooms (
    "room_id" SERIAL PRIMARY KEY,
    "theater_id" INTEGER NOT NULL,
    "room_name" VARCHAR(50) NOT NULL,
    "layout_id" INTEGER,
    "created_at" TIMESTAMP
    WITH
        TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        UNIQUE ("theater_id", "room_name") -- Mỗi rạp có phòng tên duy nhất
);

-- Bảng Seats (Ghế thực tế trong phòng)
CREATE TABLE seats (
    "seat_id" SERIAL PRIMARY KEY,
    "room_id" INTEGER NOT NULL,
    "row_number" INTEGER NOT NULL,
    "column_number" INTEGER NOT NULL,
    "seat_code" VARCHAR(10) NOT NULL,
    "seat_type" seat_type DEFAULT 'regular',
    "is_edge" BOOLEAN DEFAULT FALSE,
    "is_available" BOOLEAN DEFAULT TRUE, -- Ghế có sẵn về mặt vật lý (không bị hỏng)
    "created_at" TIMESTAMP
    WITH
        TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        UNIQUE ("room_id", "seat_code") -- Đảm bảo mã ghế duy nhất trong một phòng
);

-- Bảng Showtimes (Suất chiếu)
CREATE TABLE showtimes (
    "showtime_id" SERIAL PRIMARY KEY,
    "movie_id" INTEGER NOT NULL,
    "room_id" INTEGER NOT NULL,
    "show_datetime" TIMESTAMP
    WITH
        TIME ZONE NOT NULL,
        "format" format_type NOT NULL DEFAULT 'TWO_D',
        "ticket_price" NUMERIC(10, 2) NOT NULL,
        "status" showtimes_status NOT NULL DEFAULT 'active',
        "language" language_type NOT NULL DEFAULT 'original',
        "created_at" TIMESTAMP
    WITH
        TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        "updated_at" TIMESTAMP
    WITH
        TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Bảng Transactions (Giao dịch)
CREATE TABLE transactions (
    "transaction_id" SERIAL PRIMARY KEY,
    "user_id" INTEGER, -- ID của khách hàng
    "staff_user_id" INTEGER, -- NEW: ID của nhân viên thực hiện giao dịch
    "promotion_id" INTEGER, -- Khuyến mãi áp dụng cho toàn giao dịch
    "total_amount" NUMERIC(10, 2) NOT NULL,
    "payment_method" VARCHAR(50) NOT NULL, -- Ví dụ: MoMo, CreditCard, Cash, Complimentary, POS_machine
    "transaction_time" TIMESTAMP
    WITH
        TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        "status" transaction_status DEFAULT 'pending', -- pending, success, failed
        "payment_ref_code" VARCHAR(255) -- NEW: Mã tham chiếu từ cổng thanh toán
);

-- Bảng Tickets (Vé)
CREATE TABLE tickets (
    "ticket_id" SERIAL PRIMARY KEY,
    "user_id" INTEGER, -- ID của khách hàng sở hữu vé
    "showtime_id" INTEGER NOT NULL,
    "seat_id" INTEGER NOT NULL,
    "promotion_id" INTEGER, -- Khuyến mãi áp dụng cho từng vé (nếu có)
    "price" NUMERIC(10, 2) NOT NULL, -- Giá cuối cùng của từng vé
    "booking_time" TIMESTAMP
    WITH
        TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        "status" ticket_status DEFAULT 'pending',
        "cancelled_at" TIMESTAMP
    WITH
        TIME ZONE, -- Thời điểm hủy vé
        UNIQUE ("showtime_id", "seat_id") -- Đảm bảo mỗi ghế trong một suất chiếu chỉ có một vé được xác nhận
);

-- Bảng TransactionTickets (Liên kết Giao dịch và Vé)
CREATE TABLE transaction_tickets (
    "transaction_id" INTEGER NOT NULL,
    "ticket_id" INTEGER NOT NULL,
    PRIMARY KEY ("transaction_id", "ticket_id")
);

-- Bảng TransactionCombos (Liên kết Giao dịch và Combo)
CREATE TABLE transaction_combos (
    "transaction_id" INTEGER NOT NULL,
    "combo_id" INTEGER,
    "quantity" INTEGER NOT NULL,
    PRIMARY KEY ("transaction_id", "combo_id")
);

-- Bảng SeatReservations (Giữ ghế tạm thời)
CREATE TABLE seat_reservations (
    "reservation_id" SERIAL PRIMARY KEY,
    "seat_id" INTEGER NOT NULL,
    "showtime_id" INTEGER NOT NULL,
    "user_id" INTEGER, -- ID của người dùng (nếu đăng nhập)
    "session_id" VARCHAR(255), -- NEW: ID phiên làm việc (nếu chưa đăng nhập)
    "reserved_at" TIMESTAMP
    WITH
        TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        "expires_at" TIMESTAMP
    WITH
        TIME ZONE NOT NULL, -- Thời điểm hết hạn giữ ghế
        "status" VARCHAR(50) NOT NULL DEFAULT 'pending', -- pending, confirmed, cancelled
        "transaction_id" INTEGER, -- Liên kết với giao dịch nếu đã khởi tạo
        UNIQUE ("seat_id", "showtime_id") -- Đảm bảo một ghế chỉ được giữ một lần cho một suất chiếu
);

-- Bảng Reviews
CREATE TABLE reviews (
    "review_id" SERIAL PRIMARY KEY,
    "movie_id" INTEGER NOT NULL,
    "user_id" INTEGER,
    "rating" INTEGER NOT NULL,
    "comment" TEXT,
    "created_at" TIMESTAMP
    WITH
        TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Bảng Email
CREATE TABLE email_verifications (
    "email_id" SERIAL PRIMARY KEY,
    "email" VARCHAR(255) NOT NULL,
    "verification_code" VARCHAR(255) NOT NULL,
    "is_used" BOOLEAN DEFAULT FALSE,
    "created_at" TIMESTAMP
    WITH
        TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        "expires_at" TIMESTAMP
    WITH
        TIME ZONE NOT NULL
);

-- Phần 3: Tạo Indexes (Chỉ mục)
-- Các chỉ mục giúp tăng tốc độ truy vấn

CREATE INDEX idx_combos_name ON combos (combo_name);

CREATE INDEX idx_combo_dishes_name ON combo_dishes (dish_name);

CREATE INDEX idx_combo_items_combo_id ON combo_items (combo_id);

CREATE INDEX idx_ranks_name ON ranks (rank_name);

CREATE INDEX idx_ranks_is_default ON ranks (is_default);

CREATE INDEX idx_movies_title ON movies (title);

CREATE INDEX idx_movies_status ON movies (status);

CREATE INDEX idx_theaters_city ON theaters (city);

CREATE INDEX idx_reviews_movie_id ON reviews (movie_id);

CREATE INDEX idx_showtimes_show_datetime ON showtimes (show_datetime);

CREATE INDEX idx_showtimes_movie_id ON showtimes (movie_id);

CREATE INDEX idx_showtimes_room_id ON showtimes (room_id);

CREATE INDEX ix_seat_reservations_expires_at ON seat_reservations (expires_at);

CREATE INDEX ix_seat_reservations_status ON seat_reservations (status);

CREATE INDEX ix_seat_reservations_showtime_id ON seat_reservations (showtime_id);

CREATE INDEX idx_tickets_showtime_id ON tickets (showtime_id);

CREATE INDEX idx_tickets_seat_id ON tickets (seat_id);

CREATE INDEX idx_transactions_user_id ON transactions (user_id);

CREATE INDEX idx_transactions_staff_user_id ON transactions (staff_user_id);

CREATE INDEX idx_users_email ON users (email);

CREATE INDEX idx_roles_role_name ON roles (role_name);

CREATE INDEX idx_permissions_permission_name ON permissions (permission_name);

-- Phần 4: Thêm các Ràng buộc Khóa ngoại (Foreign Keys)
-- Đảm bảo các bảng đã được tạo trước khi thêm FK

-- Thêm cột rank_id vào bảng users và ràng buộc khóa ngoại
ALTER TABLE users
ADD COLUMN rank_id INTEGER,
ADD CONSTRAINT fk_users_rank_id FOREIGN KEY (rank_id) REFERENCES ranks (rank_id) ON DELETE SET NULL;

-- Thêm khóa ngoại cho combo_id
ALTER TABLE combo_items
ADD CONSTRAINT fk_combo_items_combo_id FOREIGN KEY (combo_id) REFERENCES combos (combo_id) ON DELETE CASCADE;

-- Thêm khóa ngoại cho dish_id (liên kết với combo_dishes)
ALTER TABLE combo_items
ADD CONSTRAINT fk_combo_items_dish_id FOREIGN KEY (dish_id) REFERENCES combo_dishes (dish_id) ON DELETE CASCADE;

ALTER TABLE reviews
ADD CONSTRAINT fk_reviews_movie_id FOREIGN KEY (movie_id) REFERENCES movies (movie_id) ON DELETE CASCADE;

ALTER TABLE reviews
ADD CONSTRAINT fk_reviews_user_id FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE SET NULL;

ALTER TABLE seat_templates
ADD CONSTRAINT fk_seat_templates_layout_id FOREIGN KEY (layout_id) REFERENCES seat_layouts (layout_id) ON DELETE CASCADE;

ALTER TABLE rooms
ADD CONSTRAINT fk_rooms_theater_id FOREIGN KEY (theater_id) REFERENCES theaters (theater_id) ON DELETE CASCADE;

ALTER TABLE rooms
ADD CONSTRAINT fk_rooms_layout_id FOREIGN KEY (layout_id) REFERENCES seat_layouts (layout_id) ON DELETE SET NULL;

ALTER TABLE seats
ADD CONSTRAINT fk_seats_room_id FOREIGN KEY (room_id) REFERENCES rooms (room_id) ON DELETE CASCADE;

ALTER TABLE showtimes
ADD CONSTRAINT fk_showtimes_movie_id FOREIGN KEY (movie_id) REFERENCES movies (movie_id) ON DELETE CASCADE;

ALTER TABLE showtimes
ADD CONSTRAINT fk_showtimes_room_id FOREIGN KEY (room_id) REFERENCES rooms (room_id) ON DELETE CASCADE;

ALTER TABLE tickets
ADD CONSTRAINT fk_tickets_user_id FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE SET NULL;

ALTER TABLE tickets
ADD CONSTRAINT fk_tickets_showtime_id FOREIGN KEY (showtime_id) REFERENCES showtimes (showtime_id) ON DELETE CASCADE;

ALTER TABLE tickets
ADD CONSTRAINT fk_tickets_seat_id FOREIGN KEY (seat_id) REFERENCES seats (seat_id) ON DELETE CASCADE;

ALTER TABLE tickets
ADD CONSTRAINT fk_tickets_promotion_id FOREIGN KEY (promotion_id) REFERENCES promotions (promotion_id) ON DELETE SET NULL;

ALTER TABLE transactions
ADD CONSTRAINT fk_transactions_user_id FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE SET NULL;

ALTER TABLE transactions
ADD CONSTRAINT fk_transactions_staff_user_id FOREIGN KEY (staff_user_id) REFERENCES users (user_id) ON DELETE SET NULL;

ALTER TABLE transactions
ADD CONSTRAINT fk_transactions_promotion_id FOREIGN KEY (promotion_id) REFERENCES promotions (promotion_id) ON DELETE SET NULL;

ALTER TABLE transaction_tickets
ADD CONSTRAINT fk_transaction_tickets_transaction_id FOREIGN KEY (transaction_id) REFERENCES transactions (transaction_id) ON DELETE CASCADE;

ALTER TABLE transaction_tickets
ADD CONSTRAINT fk_transaction_tickets_ticket_id FOREIGN KEY (ticket_id) REFERENCES tickets (ticket_id) ON DELETE CASCADE;

ALTER TABLE transaction_combos
ADD CONSTRAINT fk_transaction_combos_transaction_id FOREIGN KEY (transaction_id) REFERENCES transactions (transaction_id) ON DELETE CASCADE;

ALTER TABLE transaction_combos
ADD CONSTRAINT fk_transaction_combos_combo_id FOREIGN KEY (combo_id) REFERENCES combos (combo_id) ON DELETE SET NULL;

ALTER TABLE seat_reservations
ADD CONSTRAINT fk_seat_reservations_seat_id FOREIGN KEY (seat_id) REFERENCES seats (seat_id) ON DELETE CASCADE;

ALTER TABLE seat_reservations
ADD CONSTRAINT fk_seat_reservations_showtime_id FOREIGN KEY (showtime_id) REFERENCES showtimes (showtime_id) ON DELETE CASCADE;

ALTER TABLE seat_reservations
ADD CONSTRAINT fk_seat_reservations_user_id FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE SET NULL;

ALTER TABLE seat_reservations
ADD CONSTRAINT fk_seat_reservations_transaction_id FOREIGN KEY (transaction_id) REFERENCES transactions (transaction_id) ON DELETE SET NULL;

-- Phần 5: Thêm các Ràng buộc CHECK (Kiểm tra dữ liệu)

-- Thêm các ràng buộc CHECK cho bảng ranks
ALTER TABLE ranks
ADD CONSTRAINT chk_ranks_spending_target CHECK (spending_target >= 0),

ADD CONSTRAINT chk_ranks_ticket_percent CHECK (ticket_percent >= 0 AND ticket_percent <= 100),

ADD CONSTRAINT chk_ranks_combo_percent CHECK (combo_percent >= 0 AND combo_percent <= 100);

ALTER TABLE combos
ADD CONSTRAINT chk_combos_price CHECK (price >= 0);

ALTER TABLE combo_items
ADD CONSTRAINT chk_combo_items_quantity CHECK (quantity > 0);

ALTER TABLE promotions
ADD CONSTRAINT chk_promotions_discount_percentage CHECK (
    discount_percentage >= 0
    AND discount_percentage <= 100
);

ALTER TABLE promotions
ADD CONSTRAINT chk_promotions_end_date CHECK (start_date < end_date);

ALTER TABLE promotions
ADD CONSTRAINT chk_promotions_max_usage CHECK (max_usage >= 0);

ALTER TABLE reviews
ADD CONSTRAINT chk_reviews_rating CHECK (
    rating >= 1
    AND rating <= 10
);

ALTER TABLE seat_layouts
ADD CONSTRAINT chk_seat_layouts_total_rows CHECK (total_rows > 0);

ALTER TABLE seat_layouts
ADD CONSTRAINT chk_seat_layouts_total_columns CHECK (total_columns > 0);

ALTER TABLE seats
ADD CONSTRAINT chk_seats_row_number CHECK (row_number > 0);

ALTER TABLE seats
ADD CONSTRAINT chk_seats_column_number CHECK (column_number > 0);

ALTER TABLE showtimes
ADD CONSTRAINT chk_showtimes_ticket_price CHECK (ticket_price >= 0);

ALTER TABLE tickets
ADD CONSTRAINT chk_tickets_price CHECK (price >= 0);

ALTER TABLE transactions
ADD CONSTRAINT chk_transactions_total_amount CHECK (total_amount >= 0);

ALTER TABLE transaction_combos
ADD CONSTRAINT chk_transaction_combos_quantity CHECK (quantity > 0);