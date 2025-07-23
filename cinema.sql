CREATE TYPE "age_rating_type" AS ENUM (
  'P',
  'C13',
  'C16',
  'C18'
);

CREATE TYPE "movie_status_type" AS ENUM (
  'upcoming',
  'now_showing',
  'ended'
);

CREATE TYPE "seat_type" AS ENUM (
  'regular',
  'vip',
  'couple'
);

CREATE TYPE "ticket_status" AS ENUM (
  'pending',
  'confirmed',
  'cancelled'
);

CREATE TYPE "transaction_status" AS ENUM (
  'pending',
  'success',
  'failed'
);

CREATE TYPE "user_status" AS ENUM (
  'active',
  'inactive',
  'suspended'
);

CREATE TYPE "combo_status" AS ENUM (
  'active',
  'inactive'
);

CREATE TYPE "theater_type_status" AS ENUM (
  'active',
  'inactive'
);

CREATE TYPE "user_role" AS ENUM (
  'admin',
  'theater_manager',
  'staff',
  'customer'
);
CREATE TYPE "showtimes_status" AS ENUM (
  'active',
  'inactive',
  'sold_out'
  );

CREATE TYPE "language_type" AS ENUM (
  'sub_vi',
  'sub_en',
  'dub_en',
  'dub_vi',
  'original'
);
CREATE TYPE "format_type" AS ENUM (
  'TWO_D',
  'THREE_D',
  'IMAX',
  '4DX'
);

CREATE TABLE "combos" (
  "combo_id" serial PRIMARY KEY,
  "combo_name" varchar(255) UNIQUE NOT NULL,
  "description" text,
  "price" numeric(10,2) NOT NULL,
  "status" combo_status DEFAULT 'active',
  "created_at" timestamp DEFAULT (CURRENT_TIMESTAMP)
);

CREATE TABLE "combo_items" (
  "item_id" serial PRIMARY KEY,
  "combo_id" int NOT NULL,
  "item_name" varchar(100) NOT NULL,
  "quantity" int NOT NULL
);

CREATE TABLE "movies" (
  "movie_id" serial PRIMARY KEY,
  "title" varchar(255) NOT NULL,
  "genre" varchar(100),
  "duration" int NOT NULL,
  "age_rating" age_rating_type NOT NULL,
  "language" varchar(50),
  "format" varchar(50),
  "description" text,
  "release_date" date,
  "trailer_url" varchar(255),
  "poster_url" varchar(255),
  "status" movie_status_type DEFAULT 'upcoming',
  "director" varchar(255),
  "actors" text,
  "created_at" timestamp DEFAULT (CURRENT_TIMESTAMP)
);

CREATE TABLE "promotions" (
  "promotion_id" serial PRIMARY KEY,
  "code" varchar(50) UNIQUE NOT NULL,
  "discount_percentage" numeric(5,2),
  "start_date" date NOT NULL,
  "end_date" date NOT NULL,
  "max_usage" int,
  "used_count" int DEFAULT 0,
  "description" text,
  "created_at" timestamp DEFAULT (CURRENT_TIMESTAMP)
);

CREATE TABLE "theaters" (
  "theater_id" serial PRIMARY KEY,
  "name" varchar(255) UNIQUE NOT NULL,
  "address" text NOT NULL,
  "city" varchar(100),
  "phone" varchar(20),
  "created_at" timestamp DEFAULT (CURRENT_TIMESTAMP)
);

CREATE TABLE "users" (
  "user_id" serial PRIMARY KEY,
  "full_name" varchar(255) NOT NULL,
  "email" varchar(255) UNIQUE NOT NULL,
  "phone_number" varchar(20) UNIQUE,
  "password_hash" varchar(255) NOT NULL,
  "status" user_status DEFAULT 'active',
  "role" user_role NOT NULL DEFAULT 'customer',
  "created_at" timestamp DEFAULT (CURRENT_TIMESTAMP),
  "updated_at" timestamp DEFAULT (CURRENT_TIMESTAMP)
);

CREATE TABLE "reviews" (
  "review_id" serial PRIMARY KEY,
  "movie_id" int NOT NULL,
  "user_id" int,
  "rating" int NOT NULL,
  "comment" text,
  "created_at" timestamp DEFAULT (CURRENT_TIMESTAMP)
);

CREATE TABLE "seat_layouts" (
  "layout_id" serial PRIMARY KEY,
  "layout_name" varchar(100) UNIQUE NOT NULL,
  "total_rows" int NOT NULL,
  "total_columns" int NOT NULL,
  "aisle_positions" text
);

CREATE TABLE "seat_templates" (
  "template_id" serial PRIMARY KEY,
  "layout_id" int NOT NULL,
  "row_number" int NOT NULL,
  "column_number" int NOT NULL,
  "seat_code" varchar(10) NOT NULL,
  "seat_type" seat_type DEFAULT 'regular',
  "is_edge" boolean DEFAULT false,
  "is_active" boolean DEFAULT true
);

CREATE TABLE "seats" (
  "seat_id" serial PRIMARY KEY,
  "room_id" int NOT NULL,
  "layout_id" int NOT NULL,
  "seat_type" seat_type DEFAULT 'regular',
  "seat_number" varchar(10) NOT NULL,
  "is_available" boolean DEFAULT true,
  "is_edge" boolean DEFAULT false,
  "row_number" int NOT NULL,
  "column_number" int NOT NULL,
  "created_at" timestamp DEFAULT (CURRENT_TIMESTAMP)
);

CREATE TABLE "rooms" (
  "room_id" serial PRIMARY KEY,
  "theater_id" int NOT NULL,
  "room_name" varchar(50) NOT NULL,
  "layout_id" int,
  "created_at" timestamp DEFAULT (CURRENT_TIMESTAMP)
);

CREATE TABLE "showtimes" (
  "showtime_id" serial PRIMARY KEY,
  "movie_id" int NOT NULL,
  "room_id" int NOT NULL,
  "show_datetime" timestamptz NOT NULL,
  "format" format_type NOT NULL DEFAULT 'TWO_D',
  "ticket_price" numeric(10,2) NOT NULL,
  "status" showtimes_status NOT NULL DEFAULT 'active',
  "language" language_type NOT NULL DEFAULT 'original',
  "available_seats" int,
  "created_at" timestamp DEFAULT (CURRENT_TIMESTAMP),
  "updated_at" timestamp DEFAULT (CURRENT_TIMESTAMP)
);

CREATE TABLE "tickets" (
  "ticket_id" serial PRIMARY KEY,
  "user_id" int,
  "showtime_id" int NOT NULL,
  "seat_id" int NOT NULL,
  "promotion_id" int,
  "price" numeric(10,2) NOT NULL,
  "booking_time" timestamp DEFAULT (CURRENT_TIMESTAMP),
  "status" ticket_status DEFAULT 'pending',
  "cancelled_at" timestamp
);

CREATE TABLE "transactions" (
  "transaction_id" serial PRIMARY KEY,
  "user_id" int,
  "total_amount" numeric(10,2) NOT NULL,
  "payment_method" varchar(50),
  "transaction_time" timestamp DEFAULT (CURRENT_TIMESTAMP),
  "status" transaction_status DEFAULT 'pending'
);

CREATE TABLE "transaction_tickets" (
  "transaction_id" int NOT NULL,
  "ticket_id" int NOT NULL
);

CREATE TABLE "transaction_combos" (
  "transaction_id" int NOT NULL,
  "combo_id" int,
  "quantity" int NOT NULL
);
CREATE INDEX ON "movies" ("title");
CREATE INDEX ON "movies" ("status");
CREATE INDEX ON "theaters" ("city");
CREATE INDEX ON "users" ("role");
CREATE INDEX ON "reviews" ("movie_id");
CREATE UNIQUE INDEX ON "seat_templates" ("layout_id", "seat_code");
CREATE UNIQUE INDEX ON "seats" ("room_id", "seat_number");
CREATE INDEX ON "showtimes" ("show_datetime");
CREATE INDEX ON "showtimes" ("movie_id");
CREATE INDEX ON "showtimes" ("room_id");
CREATE UNIQUE INDEX ON "transaction_tickets" ("transaction_id", "ticket_id");
CREATE UNIQUE INDEX ON "transaction_combos" ("transaction_id", "combo_id");
COMMENT ON COLUMN "combos"."price" IS 'CHECK (price >= 0)';
COMMENT ON COLUMN "combo_items"."combo_id" IS 'References combos.combo_id';
COMMENT ON COLUMN "combo_items"."quantity" IS 'CHECK (quantity > 0)';
COMMENT ON COLUMN "promotions"."discount_percentage" IS 'CHECK (discount_percentage >= 0 AND discount_percentage <= 100)';
COMMENT ON COLUMN "promotions"."end_date" IS 'CHECK (start_date < end_date)';
COMMENT ON COLUMN "promotions"."max_usage" IS 'CHECK (max_usage >= 0)';
COMMENT ON COLUMN "reviews"."rating" IS 'CHECK (rating >= 1 AND rating <= 10)';
COMMENT ON COLUMN "seat_layouts"."total_rows" IS 'CHECK (total_rows > 0)';
COMMENT ON COLUMN "seat_layouts"."total_columns" IS 'CHECK (total_columns > 0)';
COMMENT ON COLUMN "seat_layouts"."aisle_positions" IS 'JSON array of aisle positions: [{"row": 5, "col": 3}]';
COMMENT ON COLUMN "seats"."row_number" IS 'CHECK (row_number > 0)';
COMMENT ON COLUMN "seats"."column_number" IS 'CHECK (column_number > 0)';
COMMENT ON COLUMN "showtimes"."ticket_price" IS 'CHECK (ticket_price >= 0)';
COMMENT ON COLUMN "tickets"."price" IS 'CHECK (price >= 0)';
COMMENT ON COLUMN "transactions"."total_amount" IS 'CHECK (total_amount >= 0)';
COMMENT ON COLUMN "transaction_combos"."quantity" IS 'CHECK (quantity > 0)';
ALTER TABLE "seat_templates" ADD FOREIGN KEY ("layout_id") REFERENCES "seat_layouts" ("layout_id");
ALTER TABLE "combo_items" ADD FOREIGN KEY ("combo_id") REFERENCES "combos" ("combo_id") ON DELETE CASCADE;
ALTER TABLE "reviews" ADD FOREIGN KEY ("movie_id") REFERENCES "movies" ("movie_id") ON DELETE CASCADE;
ALTER TABLE "reviews" ADD FOREIGN KEY ("user_id") REFERENCES "users" ("user_id") ON DELETE SET NULL;
ALTER TABLE "rooms" ADD FOREIGN KEY ("theater_id") REFERENCES "theaters" ("theater_id") ON DELETE CASCADE;
ALTER TABLE "rooms" ADD FOREIGN KEY ("layout_id") REFERENCES "seat_layouts" ("layout_id") ON DELETE SET NULL;
ALTER TABLE "seats" ADD FOREIGN KEY ("room_id") REFERENCES "rooms" ("room_id") ON DELETE CASCADE;
ALTER TABLE "showtimes" ADD FOREIGN KEY ("movie_id") REFERENCES "movies" ("movie_id") ON DELETE CASCADE;
ALTER TABLE "showtimes" ADD FOREIGN KEY ("room_id") REFERENCES "rooms" ("room_id") ON DELETE CASCADE;
ALTER TABLE "tickets" ADD FOREIGN KEY ("user_id") REFERENCES "users" ("user_id") ON DELETE SET NULL;
ALTER TABLE "tickets" ADD FOREIGN KEY ("showtime_id") REFERENCES "showtimes" ("showtime_id") ON DELETE CASCADE;
ALTER TABLE "tickets" ADD FOREIGN KEY ("seat_id") REFERENCES "seats" ("seat_id") ON DELETE CASCADE;
ALTER TABLE "tickets" ADD FOREIGN KEY ("promotion_id") REFERENCES "promotions" ("promotion_id") ON DELETE SET NULL;
ALTER TABLE "transactions" ADD FOREIGN KEY ("user_id") REFERENCES "users" ("user_id") ON DELETE SET NULL;
ALTER TABLE "transaction_tickets" ADD FOREIGN KEY ("transaction_id") REFERENCES "transactions" ("transaction_id") ON DELETE CASCADE;
ALTER TABLE "transaction_tickets" ADD FOREIGN KEY ("ticket_id") REFERENCES "tickets" ("ticket_id") ON DELETE CASCADE;
ALTER TABLE "transaction_combos" ADD FOREIGN KEY ("transaction_id") REFERENCES "transactions" ("transaction_id") ON DELETE CASCADE;
ALTER TABLE "transaction_combos" ADD FOREIGN KEY ("combo_id") REFERENCES "combos" ("combo_id") ON DELETE SET NULL;
