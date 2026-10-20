CREATE TABLE orders (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id INTEGER,
    order_date DATE,
    item_id INTEGER REFERENCES product_catalog(item_id),
    quantity INTEGER
);