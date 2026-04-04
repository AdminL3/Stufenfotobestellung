-- ── RESET ─────────────────────────────────────────────────────────────────────
DROP TABLE IF EXISTS order_images CASCADE;
DROP TABLE IF EXISTS orders CASCADE;

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
    gk_tpy            text[],
    mottowoche        int[],
    stufenfotos       int[],
    extra_photos      int DEFAULT 0,
    image_count       int DEFAULT 0,
    extra_cost        numeric(6,2) DEFAULT 0,
    paid              boolean DEFAULT false,
    archived          boolean DEFAULT false
);

ALTER TABLE orders DISABLE ROW LEVEL SECURITY;

-- ── IMAGES TABLE ──────────────────────────────────────────────────────────────
CREATE TABLE order_images (
    id          uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    created_at  timestamptz DEFAULT now(),
    order_id    uuid NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    url         text NOT NULL,
    filename    text,
    position    int
);

ALTER TABLE order_images DISABLE ROW LEVEL SECURITY;

-- ── CONFIG TABLE ──────────────────────────────────────────────────────────────
CREATE TABLE config (
    key    text PRIMARY KEY,
    value  text NOT NULL
);

ALTER TABLE config DISABLE ROW LEVEL SECURITY;

INSERT INTO config (key, value) VALUES
    ('MAX_IMAGES',                          '20'),
    ('NORMAL_IMAGE_PRICE',                  '0.25'),
    ('UPLOAD_PHOTO_PRICE',                  '0.49'),
    ('AMOUNT_OF_FREE_IMAGES',               '2'),
    ('PRINTING_COST',                       '0.14')
ON CONFLICT (key) DO NOTHING;

-- ── GRANTS ────────────────────────────────────────────────────────────────────
GRANT USAGE ON SCHEMA public TO anon;
GRANT INSERT, SELECT ON TABLE orders TO anon;
GRANT INSERT, SELECT ON TABLE order_images TO anon;
GRANT SELECT ON TABLE config TO anon;

-- Admin needs UPDATE for payments, archiving, and config changes
GRANT UPDATE ON TABLE orders TO anon;
GRANT UPDATE ON TABLE config TO anon;