-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║  FOTOBESTELLUNG                                                           ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝

-- ── RESET ─────────────────────────────────────────────────────────────────────
DROP TABLE IF EXISTS order_images CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS config;

-- ── STORAGE BUCKET ────────────────────────────────────────────────────────────
INSERT INTO storage.buckets (id, name, public)
VALUES ('images', 'images', true)
ON CONFLICT (id) DO NOTHING;

DROP POLICY IF EXISTS "Allow anon uploads" ON storage.objects;
CREATE POLICY "Allow anon uploads"
ON storage.objects FOR INSERT
TO anon
WITH CHECK (bucket_id = 'images');

DROP POLICY IF EXISTS "Allow public reads" ON storage.objects;
CREATE POLICY "Allow public reads"
ON storage.objects FOR SELECT
TO anon
USING (bucket_id = 'images');

-- ── ORDERS TABLE ──────────────────────────────────────────────────────────────
CREATE TABLE orders (
    id                uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    created_at        timestamptz DEFAULT now(),
    name              text NOT NULL,
    leistungskurs     text,
    lk_typ            text[],
    grundkurs         text,
    gk_typ            text[],
    mottowoche        int[],
    stufenfotos       int[],
    extra_photos      int DEFAULT 0,
    image_count       int DEFAULT 0,
    paid              boolean DEFAULT false,
    archived          boolean DEFAULT false
);

ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow anon all" ON orders;
CREATE POLICY "Allow anon all"
ON orders FOR ALL TO anon
USING (true) WITH CHECK (true);

GRANT USAGE ON SCHEMA public TO anon;
GRANT INSERT, SELECT, UPDATE ON TABLE orders TO anon;

-- ── IMAGES TABLE ──────────────────────────────────────────────────────────────
CREATE TABLE order_images (
    id          uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    created_at  timestamptz DEFAULT now(),
    order_id    uuid NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    url         text NOT NULL,
    filename    text,
    position    int
);

ALTER TABLE order_images ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow anon all" ON order_images;
CREATE POLICY "Allow anon all"
ON order_images FOR ALL TO anon
USING (true) WITH CHECK (true);

GRANT INSERT, SELECT ON TABLE order_images TO anon;

-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║  CONFIG                                                                   ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝
CREATE TABLE config (
    key    text PRIMARY KEY,
    value  text NOT NULL
);

ALTER TABLE config ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow anon all" ON config;
CREATE POLICY "Allow anon all"
ON config FOR ALL TO anon
USING (true) WITH CHECK (true);

GRANT SELECT, UPDATE ON TABLE config TO anon;

INSERT INTO config (key, value) VALUES
    ('MAX_IMAGES',              '20'),
    ('NORMAL_IMAGE_PRICE',      '0.20'),
    ('UPLOAD_PHOTO_PRICE',      '0.40'),
    ('AMOUNT_OF_FREE_IMAGES',   '2'),
    ('PRINTING_COST',           '0.14')
ON CONFLICT (key) DO NOTHING;

-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║  ABIMERCH                                                                 ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝

-- ── RESET ─────────────────────────────────────────────────────────────────────
DROP TABLE IF EXISTS abimerch CASCADE;

-- ── ABIMERCH TABLE ────────────────────────────────────────────────────────────
CREATE TABLE abimerch (
    id           uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    created_at   timestamptz DEFAULT now(),
    name         text NOT NULL,
    size         text NOT NULL,
    color        text NOT NULL,
    design_image text
);

ALTER TABLE abimerch ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow anon all" ON abimerch;
CREATE POLICY "Allow anon all"
ON abimerch FOR ALL TO anon
USING (true) WITH CHECK (true);

GRANT USAGE ON SCHEMA public TO anon;
GRANT INSERT, SELECT, UPDATE ON TABLE abimerch TO anon;