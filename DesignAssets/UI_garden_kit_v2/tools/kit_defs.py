# -*- coding: utf-8 -*-
"""Element definitions for the BlockOut home (garden map) screen kit.

All coordinates are in the 941x1672 reference screenshot's pixel space.
"""

SRC = 'reference.jpg'

# name, crop box, silhouette shapes, options
ELEMENTS = [
    ('btn_settings', (40, 38, 168, 168),
     [('circle', 104, 103, 52)], {'desky': True}),

    ('pill_currency', (650, 48, 928, 160),
     [('rr', 663, 61, 915, 147, 43)], {'desky': True}),

    ('btn_task', (726, 228, 920, 450),
     [('circle', 820, 318, 78), ('rr', 754, 374, 894, 431, 24)], {'desky': True}),

    ('btn_achievement', (726, 473, 920, 694),
     [('circle', 820, 562, 78), ('rr', 754, 618, 894, 675, 24)], {'desky': True}),

    ('node_locked_40', (386, 38, 578, 230),
     [('rr', 404, 56, 553, 196, 38), ('circle', 525, 165, 32)], {'desky': True}),

    ('node_locked_39', (386, 256, 578, 434),
     [('rr', 404, 272, 551, 408, 38), ('circle', 523, 388, 32)], {'desky': True}),

    ('node_star_38', (386, 493, 582, 692),
     [('rr', 397, 508, 544, 642, 38), ('circle', 520, 628, 34)], {'desky': True}),

    ('node_current_37', (350, 698, 582, 978),
     [('rr', 379, 737, 555, 921, 48), ('poly', [(436, 900), (496, 900), (466, 956)])], {'desky': True}),

    ('node_fail_36', (183, 953, 362, 1142),
     [('rr', 207, 999, 338, 1086, 34), ('circle', 272, 1093, 31)], {'desky': True}),

    ('node_challenge', (578, 953, 767, 1142),
     [('rr', 599, 1001, 729, 1086, 34), ('circle', 664, 1093, 31)], {'desky': True}),

    ('bubble_current', (543, 683, 710, 797),
     [('rr', 557, 699, 693, 759, 26), ('poly', [(566, 752), (598, 760), (574, 784)])], {'desky': True}),

    ('mascot_arrow', (370, 934, 540, 1092),
     [('rr', 413, 945, 501, 1077, 14),
      ('rr', 398, 949, 418, 983, 3), ('rr', 388, 991, 412, 1021, 3),
      ('rr', 383, 1025, 403, 1051, 3), ('rr', 398, 1053, 418, 1081, 3),
      ('rr', 499, 959, 521, 987, 3), ('rr', 499, 993, 521, 1023, 3),
      ('rr', 499, 1027, 525, 1053, 3), ('rr', 499, 1055, 519, 1081, 3)], {}),

    ('btn_primary', (184, 1134, 756, 1394),
     [('rr', 207, 1165, 731, 1377, 104)], {'degrass': 5}),

    ('nav_bar', (38, 1436, 904, 1672),
     [('rr', 61, 1456, 880, 1658, 54)], {'degrass': 7}),
]

# tab crops keep their little cream card so they can sit on nav_bar_empty
TABS = [
    ('tab_home', (74, 1464, 266, 1654), 30),
    ('tab_gallery', (284, 1464, 476, 1654), 30),
    ('tab_skin', (494, 1464, 686, 1654), 30),
    ('tab_daily', (702, 1464, 878, 1654), 30),
]

# navigation glyphs cut tight (no cream), for the runtime nav bar
NAV_GLYPHS = [
    ('glyph_home', (108, 1452, 228, 1572), [('circle', 168, 1510, 58)]),
    ('glyph_gallery', (318, 1452, 438, 1572), [('circle', 378, 1510, 58)]),
    ('glyph_skin', (528, 1452, 648, 1572), [('circle', 588, 1510, 58)]),
    ('glyph_daily', (736, 1452, 856, 1572), [('circle', 796, 1510, 58)]),
]
