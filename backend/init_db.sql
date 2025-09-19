-- Создание таблицы room_types
CREATE TABLE IF NOT EXISTS room_types (
    id VARCHAR(50) PRIMARY KEY,  -- Используем ID из TravelLine API
    name VARCHAR(255) NOT NULL,
    description TEXT,
    size_value FLOAT,
    category_code VARCHAR(100),
    category_name VARCHAR(255),
    position INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Создание таблицы room_type_images
CREATE TABLE IF NOT EXISTS room_type_images (
    id SERIAL PRIMARY KEY,
    room_type_id VARCHAR(50) NOT NULL,  -- Изменяем тип на VARCHAR
    url VARCHAR(1024) NOT NULL,
    position INTEGER,
    FOREIGN KEY (room_type_id) REFERENCES room_types(id) ON DELETE CASCADE
);

-- Создание таблицы amenities
CREATE TABLE IF NOT EXISTS amenities (
    id SERIAL PRIMARY KEY,
    room_type_id VARCHAR(50) NOT NULL,  -- Изменяем тип на VARCHAR
    code VARCHAR(100) NOT NULL,
    FOREIGN KEY (room_type_id) REFERENCES room_types(id) ON DELETE CASCADE
);

-- Создание таблицы addresses
CREATE TABLE IF NOT EXISTS addresses (
    id SERIAL PRIMARY KEY,
    room_type_id VARCHAR(50) NOT NULL UNIQUE,  -- Изменяем тип на VARCHAR
    postal_code VARCHAR(50),
    country_code VARCHAR(10),
    region VARCHAR(255),
    region_id VARCHAR(50),
    city_name VARCHAR(255),
    city_id VARCHAR(50),
    address_line VARCHAR(512),
    latitude FLOAT,
    longitude FLOAT,
    remark TEXT,
    FOREIGN KEY (room_type_id) REFERENCES room_types(id) ON DELETE CASCADE
);

-- Создание таблицы occupancy
CREATE TABLE IF NOT EXISTS occupancy (
    id SERIAL PRIMARY KEY,
    room_type_id VARCHAR(50) NOT NULL UNIQUE,  -- Изменяем тип на VARCHAR
    adult_bed INTEGER DEFAULT 0,
    extra_bed INTEGER DEFAULT 0,
    child_without_bed INTEGER DEFAULT 0,
    FOREIGN KEY (room_type_id) REFERENCES room_types(id) ON DELETE CASCADE
);

-- Создание таблицы placements
CREATE TABLE IF NOT EXISTS placements (
    id SERIAL PRIMARY KEY,
    room_type_id VARCHAR(50) NOT NULL,  -- Изменяем тип на VARCHAR
    kind VARCHAR(50) NOT NULL,
    count INTEGER NOT NULL,
    min_age INTEGER,
    max_age INTEGER,
    FOREIGN KEY (room_type_id) REFERENCES room_types(id) ON DELETE CASCADE
);

-- Создание индексов для улучшения производительности
CREATE INDEX IF NOT EXISTS idx_room_type_images_room_type_id ON room_type_images(room_type_id);
CREATE INDEX IF NOT EXISTS idx_amenities_room_type_id ON amenities(room_type_id);
CREATE INDEX IF NOT EXISTS idx_placements_room_type_id ON placements(room_type_id);

-- Создание триггера для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_room_types_updated_at ON room_types;
CREATE TRIGGER update_room_types_updated_at 
    BEFORE UPDATE ON room_types 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
