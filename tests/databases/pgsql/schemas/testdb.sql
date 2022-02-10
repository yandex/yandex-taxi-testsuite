CREATE TABLE foo (
  id SERIAL PRIMARY KEY,
  value VARCHAR(255) NOT NULL
);

CREATE TABLE no_clean_table (
  id SERIAL PRIMARY KEY,
  value VARCHAR(255) NOT NULL
);

INSERT INTO no_clean_table (id, value) VALUES (1, 'one');
INSERT INTO no_clean_table (id, value) VALUES (2, 'two');
