CREATE TABLE foo (
    id Int NOT NULL,
    value String NOT NULL
) engine = MergeTree() PRIMARY KEY id;
