-- Complete partially seeded databases without changing existing IDs or products.
CREATE TEMP TABLE category_seed_006 (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    parent_id INTEGER
);

INSERT INTO category_seed_006 (id, name, parent_id) VALUES
    (1, 'Süt Ürünleri ve Kahvaltılık', NULL),
    (2, 'Et, Tavuk ve Balık', NULL),
    (3, 'Meyve ve Sebze', NULL),
    (4, 'Temel Gıda', NULL),
    (5, 'Atıştırmalık ve Tatlı', NULL),
    (6, 'İçecek', NULL),
    (7, 'Temizlik ve Kişisel Bakım Ürünleri', NULL),
    (8, 'Meyve', 3),
    (9, 'Sebze', 3),
    (10, 'Kırmızı Et', 2),
    (11, 'Beyaz Et', 2),
    (12, 'Deniz Ürünleri', 2),
    (13, 'Şarküteri', 2),
    (14, 'Sakatat', 2),
    (15, 'Süt', 1),
    (16, 'Yumurta', 1),
    (17, 'Peynir', 1),
    (18, 'Yoğurt', 1),
    (19, 'Zeytin', 1),
    (20, 'Tereyağı ve Margarin', 1),
    (21, 'Sürülebilir Ürünler ve Kahvaltılık Soslar', 1),
    (22, 'Helva Tahin ve Pekmez', 1),
    (23, 'Bal ve Reçel', 1),
    (24, 'Kahvaltılık Gevrek Bar ve Granola', 1),
    (25, 'Kaymak ve Krema', 1),
    (26, 'Ekmek ve Unlu Mamüller', 4),
    (27, 'Sıvı Yağlar', 4),
    (28, 'Bakliyat', 4),
    (29, 'Şeker ve Tatlandırıcılar', 4),
    (30, 'Mantı Makarna ve Erişte', 4),
    (31, 'Ketçap Mayonez Sos ve Sirkeler', 4),
    (32, 'Salça', 4),
    (33, 'Turşu', 4),
    (34, 'Konserve', 4),
    (35, 'Hazır Gıda', 4),
    (36, 'Bebek Mamaları', 4),
    (37, 'Un ve İrmik', 4),
    (38, 'Pasta Malzemeleri', 4),
    (39, 'Tuz Baharat ve Harçlar', 4),
    (40, 'Su', 6),
    (41, 'Meyve Suyu', 6),
    (42, 'Gazlı İçecekler', 6),
    (43, 'Gazsız İçecekler', 6),
    (44, 'Ayran ve Kefir', 6),
    (45, 'Maden Suyu', 6),
    (46, 'Çay ve Bitki Çayları', 6),
    (47, 'Kahve', 6),
    (48, 'Çikolata', 5),
    (49, 'Gofret', 5),
    (50, 'Bisküvi ve Kraker', 5),
    (51, 'Kek', 5),
    (52, 'Cips', 5),
    (53, 'Kuruyemiş ve Kuru Meyve', 5),
    (54, 'Sakız ve Şekerleme', 5),
    (55, 'Tatlılar', 5),
    (56, 'Dondurmalar', 5),
    (57, 'Bulaşık Temizlik Ürünleri', 7),
    (58, 'Çamaşır Temizlik Ürünleri', 7),
    (59, 'Genel Temizlik Ürünleri', 7),
    (60, 'Mutfak Sarf Malzemeleri', 7),
    (61, 'Tuvalet Kağıdı', 7),
    (62, 'Kağıt Havlu', 7),
    (63, 'Kağıt Peçete ve Mendil', 7),
    (64, 'Islak Mendil', 7),
    (65, 'Saç Bakım', 7),
    (66, 'Duş Banyo ve Sabun', 7),
    (67, 'Ağız Bakım', 7),
    (68, 'Hijyenik Ped', 7),
    (69, 'Bebek ve Hasta Bezi', 7),
    (70, 'Parfüm Deodorant Kolonya ve Kokular', 7),
    (71, 'Cilt Bakımı', 7),
    (72, 'Makyaj', 7),
    (73, 'Diğer Temizlik ve Kişisel Bakım Ürünleri', 7);

INSERT INTO category (name, parent_id)
SELECT seed.name, NULL
FROM category_seed_006 AS seed
WHERE seed.parent_id IS NULL
  AND NOT EXISTS (
      SELECT 1 FROM category AS existing
      WHERE existing.parent_id IS NULL AND existing.name = seed.name
  )
ORDER BY seed.id;

INSERT INTO category (name, parent_id)
SELECT child.name, (
    SELECT MIN(existing.id) FROM category AS existing
    WHERE existing.parent_id IS NULL AND existing.name = parent.name
)
FROM category_seed_006 AS child
JOIN category_seed_006 AS parent ON parent.id = child.parent_id
WHERE NOT EXISTS (
    SELECT 1 FROM category AS existing
    JOIN category AS existing_parent ON existing_parent.id = existing.parent_id
    WHERE existing.name = child.name
      AND existing_parent.parent_id IS NULL AND existing_parent.name = parent.name
)
ORDER BY child.id;

DROP TABLE category_seed_006;
