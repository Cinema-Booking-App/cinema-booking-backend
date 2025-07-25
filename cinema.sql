-- Phần 1: Tạo các kiểu dữ liệu ENUM
-- Các câu lệnh này sẽ gây lỗi nếu kiểu ENUM đã tồn tại.

CREATE TYPE age_rating_type AS ENUM ('P', 'C13', 'C16', 'C18');
CREATE TYPE movie_status_type AS ENUM ('upcoming', 'now_showing', 'ended');
CREATE TYPE seat_type AS ENUM ('regular', 'vip', 'couple');
CREATE TYPE ticket_status AS ENUM ('pending', 'confirmed', 'cancelled');
CREATE TYPE transaction_status AS ENUM ('pending', 'success', 'failed');
CREATE TYPE user_status AS ENUM ('active', 'inactive', 'suspended');
CREATE TYPE combo_status AS ENUM ('active', 'inactive');
CREATE TYPE theater_type_status AS ENUM ('active', 'inactive');
CREATE TYPE user_role AS ENUM ('admin', 'theater_manager', 'staff', 'customer');
CREATE TYPE showtimes_status AS ENUM ('active', 'inactive', 'sold_out');
CREATE TYPE language_type AS ENUM ('sub_vi', 'sub_en', 'dub_en', 'dub_vi', 'original');
CREATE TYPE format_type AS ENUM ('TWO_D', 'THREE_D', 'IMAX', '4DX');


-- Phần 2: Tạo các Bảng
-- Sắp xếp thứ tự tạo bảng để các khóa ngoại có thể tham chiếu đến các bảng đã tồn tại
-- Sử dụng IF NOT EXISTS để tránh lỗi nếu bảng đã tồn tại

-- Bảng Users
CREATE TABLE IF NOT EXISTS users (
    "user_id" SERIAL PRIMARY KEY,
    "full_name" VARCHAR(255) NOT NULL,
    "email" VARCHAR(255) UNIQUE NOT NULL,
    "phone_number" VARCHAR(20) UNIQUE,
    "password_hash" VARCHAR(255) NOT NULL,
    "status" user_status DEFAULT 'active',
    "role" user_role NOT NULL DEFAULT 'customer',
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Bảng Theaters (Rạp chiếu phim)
CREATE TABLE IF NOT EXISTS theaters (
    "theater_id" SERIAL PRIMARY KEY,
    "name" VARCHAR(255) UNIQUE NOT NULL,
    "address" TEXT NOT NULL,
    "city" VARCHAR(100),
    "phone" VARCHAR(20),
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Bảng Movies (Phim)
CREATE TABLE IF NOT EXISTS movies (
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
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Bảng Promotions (Khuyến mãi)
CREATE TABLE IF NOT EXISTS promotions (
    "promotion_id" SERIAL PRIMARY KEY,
    "code" VARCHAR(50) UNIQUE NOT NULL,
    "discount_percentage" NUMERIC(5, 2),
    "start_date" DATE NOT NULL,
    "end_date" DATE NOT NULL,
    "max_usage" INTEGER,
    "used_count" INTEGER DEFAULT 0,
    "description" TEXT,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Bảng Combos
CREATE TABLE IF NOT EXISTS combos (
    "combo_id" SERIAL PRIMARY KEY,
    "combo_name" VARCHAR(255) UNIQUE NOT NULL,
    "description" TEXT,
    "price" NUMERIC(10,2) NOT NULL,
    "status" combo_status DEFAULT 'active',
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Bảng ComboItems (Chi tiết các thành phần trong Combo)
CREATE TABLE IF NOT EXISTS combo_items (
    "item_id" SERIAL PRIMARY KEY,
    "combo_id" INTEGER NOT NULL,
    "item_name" VARCHAR(100) NOT NULL,
    "quantity" INTEGER NOT NULL
);

-- Bảng SeatLayouts (Bố cục ghế)
CREATE TABLE IF NOT EXISTS seat_layouts (
    "layout_id" SERIAL PRIMARY KEY,
    "layout_name" VARCHAR(100) UNIQUE NOT NULL,
    "total_rows" INTEGER NOT NULL,
    "total_columns" INTEGER NOT NULL,
    "aisle_positions" TEXT, -- Lưu dưới dạng JSON string
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Bảng SeatTemplates (Mẫu ghế cho bố cục)
CREATE TABLE IF NOT EXISTS seat_templates (
    "template_id" SERIAL PRIMARY KEY,
    "layout_id" INTEGER NOT NULL,
    "row_number" INTEGER NOT NULL,
    "column_number" INTEGER NOT NULL,
    "seat_code" VARCHAR(10) NOT NULL,
    "seat_type" seat_type DEFAULT 'regular',
    "is_edge" BOOLEAN DEFAULT FALSE,
    "is_active" BOOLEAN DEFAULT TRUE,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE ("layout_id", "seat_code") -- Đảm bảo mã ghế duy nhất trong một bố cục
);

-- Bảng Rooms (Phòng chiếu)
CREATE TABLE IF NOT EXISTS rooms (
    "room_id" SERIAL PRIMARY KEY,
    "theater_id" INTEGER NOT NULL,
    "room_name" VARCHAR(50) NOT NULL,
    "layout_id" INTEGER,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE ("theater_id", "room_name") -- Mỗi rạp có phòng tên duy nhất
);

-- Bảng Seats (Ghế thực tế trong phòng)
CREATE TABLE IF NOT EXISTS seats (
    "seat_id" SERIAL PRIMARY KEY,
    "room_id" INTEGER NOT NULL,
    "row_number" INTEGER NOT NULL,
    "column_number" INTEGER NOT NULL,
    "seat_code" VARCHAR(10) NOT NULL,
    "seat_type" seat_type DEFAULT 'regular',
    "is_edge" BOOLEAN DEFAULT FALSE,
    "is_available" BOOLEAN DEFAULT TRUE, -- Ghế có sẵn về mặt vật lý (không bị hỏng)
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE ("room_id", "seat_code") -- Đảm bảo mã ghế duy nhất trong một phòng
);

-- Bảng Showtimes (Suất chiếu)
CREATE TABLE IF NOT EXISTS showtimes (
    "showtime_id" SERIAL PRIMARY KEY,
    "movie_id" INTEGER NOT NULL,
    "room_id" INTEGER NOT NULL,
    "show_datetime" TIMESTAMP WITH TIME ZONE NOT NULL,
    "format" format_type NOT NULL DEFAULT 'TWO_D',
    "ticket_price" NUMERIC(10, 2) NOT NULL,
    "status" showtimes_status NOT NULL DEFAULT 'active',
    "language" language_type NOT NULL DEFAULT 'original',
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Bảng Transactions (Giao dịch)
CREATE TABLE IF NOT EXISTS transactions (
    "transaction_id" SERIAL PRIMARY KEY,
    "user_id" INTEGER, -- ID của khách hàng
    "staff_user_id" INTEGER, -- NEW: ID của nhân viên thực hiện giao dịch
    "promotion_id" INTEGER, -- Khuyến mãi áp dụng cho toàn giao dịch
    "total_amount" NUMERIC(10, 2) NOT NULL,
    "payment_method" VARCHAR(50) NOT NULL, -- Ví dụ: MoMo, CreditCard, Cash, Complimentary, POS_machine
    "transaction_time" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    "status" transaction_status DEFAULT 'pending', -- pending, success, failed
    "payment_ref_code" VARCHAR(255) -- NEW: Mã tham chiếu từ cổng thanh toán
);

-- Bảng Tickets (Vé)
CREATE TABLE IF NOT EXISTS tickets (
    "ticket_id" SERIAL PRIMARY KEY,
    "user_id" INTEGER, -- ID của khách hàng sở hữu vé
    "showtime_id" INTEGER NOT NULL,
    "seat_id" INTEGER NOT NULL,
    "promotion_id" INTEGER, -- Khuyến mãi áp dụng cho từng vé (nếu có)
    "price" NUMERIC(10, 2) NOT NULL, -- Giá cuối cùng của từng vé
    "booking_time" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    "status" ticket_status DEFAULT 'pending',
    "cancelled_at" TIMESTAMP WITH TIME ZONE, -- Thời điểm hủy vé
    UNIQUE ("showtime_id", "seat_id") -- Đảm bảo mỗi ghế trong một suất chiếu chỉ có một vé được xác nhận
);

-- Bảng TransactionTickets (Liên kết Giao dịch và Vé)
CREATE TABLE IF NOT EXISTS transaction_tickets (
    "transaction_id" INTEGER NOT NULL,
    "ticket_id" INTEGER NOT NULL,
    PRIMARY KEY ("transaction_id", "ticket_id")
);

-- Bảng TransactionCombos (Liên kết Giao dịch và Combo)
CREATE TABLE IF NOT EXISTS transaction_combos (
    "transaction_id" INTEGER NOT NULL,
    "combo_id" INTEGER,
    "quantity" INTEGER NOT NULL,
    PRIMARY KEY ("transaction_id", "combo_id")
);

-- Bảng SeatReservations (Giữ ghế tạm thời)
CREATE TABLE IF NOT EXISTS seat_reservations (
    "reservation_id" SERIAL PRIMARY KEY,
    "seat_id" INTEGER NOT NULL,
    "showtime_id" INTEGER NOT NULL,
    "user_id" INTEGER, -- ID của người dùng (nếu đăng nhập)
    "session_id" VARCHAR(255), -- NEW: ID phiên làm việc (nếu chưa đăng nhập)
    "reserved_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    "expires_at" TIMESTAMP WITH TIME ZONE NOT NULL, -- Thời điểm hết hạn giữ ghế
    "status" VARCHAR(50) NOT NULL DEFAULT 'pending', -- pending, confirmed, cancelled
    "transaction_id" INTEGER, -- Liên kết với giao dịch nếu đã khởi tạo
    UNIQUE ("seat_id", "showtime_id") -- Đảm bảo một ghế chỉ được giữ một lần cho một suất chiếu
);

-- Bảng Reviews
CREATE TABLE IF NOT EXISTS reviews (
    "review_id" SERIAL PRIMARY KEY,
    "movie_id" INTEGER NOT NULL,
    "user_id" INTEGER,
    "rating" INTEGER NOT NULL,
    "comment" TEXT,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Phần 3: Tạo Indexes (Chỉ mục)
-- Các chỉ mục giúp tăng tốc độ truy vấn
CREATE INDEX IF NOT EXISTS idx_movies_title ON movies (title);
CREATE INDEX IF NOT EXISTS idx_movies_status ON movies (status);
CREATE INDEX IF NOT EXISTS idx_theaters_city ON theaters (city);
CREATE INDEX IF NOT EXISTS idx_users_role ON users (role);
CREATE INDEX IF NOT EXISTS idx_reviews_movie_id ON reviews (movie_id);
CREATE INDEX IF NOT EXISTS idx_showtimes_show_datetime ON showtimes (show_datetime);
CREATE INDEX IF NOT EXISTS idx_showtimes_movie_id ON showtimes (movie_id);
CREATE INDEX IF NOT EXISTS idx_showtimes_room_id ON showtimes (room_id);
CREATE INDEX IF NOT EXISTS ix_seat_reservations_expires_at ON seat_reservations (expires_at);
CREATE INDEX IF NOT EXISTS ix_seat_reservations_status ON seat_reservations (status);
CREATE INDEX IF NOT EXISTS ix_seat_reservations_showtime_id ON seat_reservations (showtime_id);
CREATE INDEX IF NOT EXISTS idx_tickets_showtime_id ON tickets (showtime_id);
CREATE INDEX IF NOT EXISTS idx_tickets_seat_id ON tickets (seat_id);
CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions (user_id);
CREATE INDEX IF NOT EXISTS idx_transactions_staff_user_id ON transactions (staff_user_id);

-- Phần 4: Thêm các Ràng buộc Khóa ngoại (Foreign Keys)
-- Đảm bảo các bảng đã được tạo trước khi thêm FK
ALTER TABLE combo_items ADD CONSTRAINT fk_combo_items_combo_id FOREIGN KEY (combo_id) REFERENCES combos(combo_id) ON DELETE CASCADE;
ALTER TABLE reviews ADD CONSTRAINT fk_reviews_movie_id FOREIGN KEY (movie_id) REFERENCES movies(movie_id) ON DELETE CASCADE;
ALTER TABLE reviews ADD CONSTRAINT fk_reviews_user_id FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL;
ALTER TABLE seat_templates ADD CONSTRAINT fk_seat_templates_layout_id FOREIGN KEY (layout_id) REFERENCES seat_layouts(layout_id) ON DELETE CASCADE;
ALTER TABLE rooms ADD CONSTRAINT fk_rooms_theater_id FOREIGN KEY (theater_id) REFERENCES theaters(theater_id) ON DELETE CASCADE;
ALTER TABLE rooms ADD CONSTRAINT fk_rooms_layout_id FOREIGN KEY (layout_id) REFERENCES seat_layouts(layout_id) ON DELETE SET NULL;
ALTER TABLE seats ADD CONSTRAINT fk_seats_room_id FOREIGN KEY (room_id) REFERENCES rooms(room_id) ON DELETE CASCADE;
ALTER TABLE showtimes ADD CONSTRAINT fk_showtimes_movie_id FOREIGN KEY (movie_id) REFERENCES movies(movie_id) ON DELETE CASCADE;
ALTER TABLE showtimes ADD CONSTRAINT fk_showtimes_room_id FOREIGN KEY (room_id) REFERENCES rooms(room_id) ON DELETE CASCADE;
ALTER TABLE tickets ADD CONSTRAINT fk_tickets_user_id FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL;
ALTER TABLE tickets ADD CONSTRAINT fk_tickets_showtime_id FOREIGN KEY (showtime_id) REFERENCES showtimes(showtime_id) ON DELETE CASCADE;
ALTER TABLE tickets ADD CONSTRAINT fk_tickets_seat_id FOREIGN KEY (seat_id) REFERENCES seats(seat_id) ON DELETE CASCADE;
ALTER TABLE tickets ADD CONSTRAINT fk_tickets_promotion_id FOREIGN KEY (promotion_id) REFERENCES promotions(promotion_id) ON DELETE SET NULL;
ALTER TABLE transactions ADD CONSTRAINT fk_transactions_user_id FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL;
ALTER TABLE transactions ADD CONSTRAINT fk_transactions_staff_user_id FOREIGN KEY (staff_user_id) REFERENCES users(user_id) ON DELETE SET NULL;
ALTER TABLE transactions ADD CONSTRAINT fk_transactions_promotion_id FOREIGN KEY (promotion_id) REFERENCES promotions(promotion_id) ON DELETE SET NULL;
ALTER TABLE transaction_tickets ADD CONSTRAINT fk_transaction_tickets_transaction_id FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id) ON DELETE CASCADE;
ALTER TABLE transaction_tickets ADD CONSTRAINT fk_transaction_tickets_ticket_id FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id) ON DELETE CASCADE;
ALTER TABLE transaction_combos ADD CONSTRAINT fk_transaction_combos_transaction_id FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id) ON DELETE CASCADE;
ALTER TABLE transaction_combos ADD CONSTRAINT fk_transaction_combos_combo_id FOREIGN KEY (combo_id) REFERENCES combos(combo_id) ON DELETE SET NULL;
ALTER TABLE seat_reservations ADD CONSTRAINT fk_seat_reservations_seat_id FOREIGN KEY (seat_id) REFERENCES seats(seat_id) ON DELETE CASCADE;
ALTER TABLE seat_reservations ADD CONSTRAINT fk_seat_reservations_showtime_id FOREIGN KEY (showtime_id) REFERENCES showtimes(showtime_id) ON DELETE CASCADE;
ALTER TABLE seat_reservations ADD CONSTRAINT fk_seat_reservations_user_id FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL;
ALTER TABLE seat_reservations ADD CONSTRAINT fk_seat_reservations_transaction_id FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id) ON DELETE SET NULL;

-- Phần 5: Thêm các Ràng buộc CHECK (Kiểm tra dữ liệu)
ALTER TABLE combos ADD CONSTRAINT chk_combos_price CHECK (price >= 0);
ALTER TABLE combo_items ADD CONSTRAINT chk_combo_items_quantity CHECK (quantity > 0);
ALTER TABLE promotions ADD CONSTRAINT chk_promotions_discount_percentage CHECK (discount_percentage >= 0 AND discount_percentage <= 100);
ALTER TABLE promotions ADD CONSTRAINT chk_promotions_end_date CHECK (start_date < end_date);
ALTER TABLE promotions ADD CONSTRAINT chk_promotions_max_usage CHECK (max_usage >= 0);
ALTER TABLE reviews ADD CONSTRAINT chk_reviews_rating CHECK (rating >= 1 AND rating <= 10);
ALTER TABLE seat_layouts ADD CONSTRAINT chk_seat_layouts_total_rows CHECK (total_rows > 0);
ALTER TABLE seat_layouts ADD CONSTRAINT chk_seat_layouts_total_columns CHECK (total_columns > 0);
ALTER TABLE seats ADD CONSTRAINT chk_seats_row_number CHECK (row_number > 0);
ALTER TABLE seats ADD CONSTRAINT chk_seats_column_number CHECK (column_number > 0);
ALTER TABLE showtimes ADD CONSTRAINT chk_showtimes_ticket_price CHECK (ticket_price >= 0);
ALTER TABLE tickets ADD CONSTRAINT chk_tickets_price CHECK (price >= 0);
ALTER TABLE transactions ADD CONSTRAINT chk_transactions_total_amount CHECK (total_amount >= 0);
ALTER TABLE transaction_combos ADD CONSTRAINT chk_transaction_combos_quantity CHECK (quantity > 0);

-- Phần 6: Thêm các COMMENT (Ghi chú)
COMMENT ON COLUMN combos.price IS 'CHECK (price >= 0)';
COMMENT ON COLUMN combo_items.combo_id IS 'References combos.combo_id';
COMMENT ON COLUMN combo_items.quantity IS 'CHECK (quantity > 0)';
COMMENT ON COLUMN promotions.discount_percentage IS 'CHECK (discount_percentage >= 0 AND discount_percentage <= 100)';
COMMENT ON COLUMN promotions.end_date IS 'CHECK (start_date < end_date)';
COMMENT ON COLUMN promotions.max_usage IS 'CHECK (max_usage >= 0)';
COMMENT ON COLUMN reviews.rating IS 'CHECK (rating >= 1 AND rating <= 10)';
COMMENT ON COLUMN seat_layouts.total_rows IS 'CHECK (total_rows > 0)';
COMMENT ON COLUMN seat_layouts.total_columns IS 'CHECK (total_columns > 0)';
COMMENT ON COLUMN seat_layouts.aisle_positions IS 'JSON array of aisle positions: [{"row": 5, "col": 3}]';
COMMENT ON COLUMN seats.row_number IS 'CHECK (row_number > 0)';
COMMENT ON COLUMN seats.column_number IS 'CHECK (column_number > 0)';
COMMENT ON COLUMN showtimes.ticket_price IS 'CHECK (ticket_price >= 0)';
COMMENT ON COLUMN tickets.price IS 'CHECK (price >= 0)';
COMMENT ON COLUMN transactions.total_amount IS 'CHECK (total_amount >= 0)';
COMMENT ON COLUMN transaction_combos.quantity IS 'CHECK (quantity > 0)';
COMMENT ON COLUMN transactions.staff_user_id IS 'ID of the staff member who performed the transaction (if applicable)';
COMMENT ON COLUMN transactions.payment_ref_code IS 'Reference code from the payment gateway';
COMMENT ON COLUMN seat_reservations.session_id IS 'Session ID of the user (especially for non-logged-in users)';