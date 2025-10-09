CREATE TYPE payment_status AS ENUM ('PENDING', 'SUCCESS', 'FAILED', 'CANCELLED');

CREATE TYPE payment_method AS ENUM ('VNPAY', 'CASH', 'MOMO', 'ZALO_PAY', 'BANK_TRANSFER');
-- Bảng Payments (Chi tiết thanh toán)
CREATE TABLE payments (
    "payment_id" SERIAL PRIMARY KEY,
    "order_id" VARCHAR(100) UNIQUE NOT NULL, -- Mã đơn hàng duy nhất
    "transaction_id" INTEGER, -- Liên kết với bảng transactions
    "vnp_transaction_no" VARCHAR(100), -- Mã giao dịch VNPay
    "amount" INTEGER NOT NULL, -- Số tiền (VNĐ)
    "payment_method" payment_method NOT NULL DEFAULT 'VNPAY',
    "payment_status" payment_status DEFAULT 'PENDING',
    
    -- VNPay specific fields
    "vnp_txn_ref" VARCHAR(100),
    "vnp_bank_code" VARCHAR(20),
    "vnp_card_type" VARCHAR(20),
    "vnp_pay_date" VARCHAR(20),
    "vnp_response_code" VARCHAR(10),
    
    -- Order information
    "order_desc" TEXT,
    "client_ip" VARCHAR(45),
    
    -- User information
    "user_id" INTEGER,
    
    -- Timestamps
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);


CREATE INDEX idx_payments_order_id ON payments (order_id);

CREATE INDEX idx_payments_transaction_id ON payments (transaction_id);

CREATE INDEX idx_payments_vnp_transaction_no ON payments (vnp_transaction_no);

CREATE INDEX idx_payments_payment_status ON payments (payment_status);

CREATE INDEX idx_payments_user_id ON payments (user_id);

CREATE INDEX idx_payments_created_at ON payments (created_at);
-- Thêm khóa ngoại cho bảng payments
ALTER TABLE payments
ADD CONSTRAINT fk_payments_transaction_id FOREIGN KEY (transaction_id) REFERENCES transactions (transaction_id) ON DELETE SET NULL;

ALTER TABLE payments
ADD CONSTRAINT fk_payments_user_id FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE SET NULL;
-- Thêm các ràng buộc CHECK cho bảng payments
ALTER TABLE payments
ADD CONSTRAINT chk_payments_amount CHECK (amount > 0);

ALTER TABLE payments
ADD CONSTRAINT chk_payments_order_id_length CHECK (LENGTH(order_id) >= 3);

-- Function để cập nhật updated_at trong bảng payments
CREATE OR REPLACE FUNCTION update_payments_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger để tự động cập nhật updated_at cho bảng payments
CREATE TRIGGER trigger_update_payments_updated_at
BEFORE UPDATE ON payments
FOR EACH ROW EXECUTE FUNCTION update_payments_updated_at();