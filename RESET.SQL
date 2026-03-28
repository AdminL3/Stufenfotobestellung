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
    covered_payments  numeric(6,2) DEFAULT 0,
    extra_cost        numeric(6,2) DEFAULT 0,
    paid              boolean DEFAULT false
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

-- ── GRANTS ────────────────────────────────────────────────────────────────────
GRANT USAGE ON SCHEMA public TO anon;
GRANT INSERT, SELECT ON TABLE orders TO anon;
GRANT INSERT, SELECT ON TABLE order_images TO anon;