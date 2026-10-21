CREATE TABLE stores (
    store_id TEXT PRIMARY KEY,
    store_name TEXT NOT NULL,
    region TEXT NOT NULL
);
CREATE TABLE products (
    product_id TEXT PRIMARY KEY,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,
    list_cost REAL NOT NULL CHECK (list_cost >= 0)
);
CREATE TABLE sales (
    sale_id TEXT PRIMARY KEY,
    sale_date TEXT NOT NULL,
    store_id TEXT NOT NULL REFERENCES stores(store_id),
    product_id TEXT NOT NULL REFERENCES products(product_id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price REAL NOT NULL CHECK (unit_price > 0),
    unit_cost REAL NOT NULL CHECK (unit_cost >= 0)
);
CREATE TABLE inventory_snapshots (
    snapshot_date TEXT NOT NULL,
    store_id TEXT NOT NULL REFERENCES stores(store_id),
    product_id TEXT NOT NULL REFERENCES products(product_id),
    units_on_hand INTEGER NOT NULL CHECK (units_on_hand >= 0),
    PRIMARY KEY (snapshot_date, store_id, product_id)
);
CREATE INDEX sales_date_idx ON sales(sale_date);
CREATE INDEX sales_product_store_idx ON sales(product_id, store_id);
