
CREATE TABLE area_names
(
    area_id INTEGER NOT NULL,
    notation_id INTEGER NOT NULL,
    area_name TEXT UNIQUE NOT NULL,
    PRIMARY KEY(area_id, notation_id)
);

INSERT INTO area_names VALUES
    (1, 0, 'ベイエリア'),
    (2, 0, '東葛飾エリア'),
    (3, 0, '北総エリア'),
    (4, 0, '九十九里エリア'),
    (5, 0, '南房総エリア'),
    (6, 0, 'かずさ・臨海エリア');
