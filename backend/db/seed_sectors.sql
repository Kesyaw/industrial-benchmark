-- ============================================================
-- SEED: 16 IDX Sectors (Bursa Efek Indonesia Classification)
-- ============================================================
INSERT INTO sectors (code, name_id, name_en, is_financial, has_inventory) VALUES
    ('CONSUMER',    'Industri Barang Konsumsi',   'Consumer Goods Industry',    FALSE, TRUE),
    ('BASIC_IND',   'Industri Dasar',              'Basic Industry',              FALSE, TRUE),
    ('CHEMICAL',    'Industri Kimia',              'Chemical Industry',           FALSE, TRUE),
    ('MISC_IND',    'Industri Rupa-rupa',          'Miscellaneous Industry',      FALSE, TRUE),
    ('INFRA',       'Infrastruktur',               'Infrastructure',              FALSE, FALSE),
    ('INVESTMENT',  'Investasi',                   'Investment',                  TRUE,  FALSE),
    ('SERVICES',    'Jasa',                        'Services',                    FALSE, FALSE),
    ('FINANCE',     'Keuangan',                    'Finance',                     TRUE,  FALSE),
    ('BANKING',     'Perbankan',                   'Banking',                     TRUE,  FALSE),
    ('CONSTRUCT',   'Pembangunan Gedung',          'Building Construction',       FALSE, TRUE),
    ('UTILITIES',   'Peralatan & Utilitas',        'Utilities',                   FALSE, FALSE),
    ('TRADE',       'Perdagangan',                 'Trade',                       FALSE, TRUE),
    ('MINING',      'Pertambangan',                'Mining',                      FALSE, FALSE),
    ('AGRI',        'Pertanian',                   'Agriculture',                 FALSE, TRUE),
    ('PROPERTY',    'Properti & Real Estat',       'Property & Real Estate',      FALSE, FALSE),
    ('TRANSPORT',   'Transportasi',                'Transportation',              FALSE, FALSE)
ON CONFLICT (code) DO NOTHING;
