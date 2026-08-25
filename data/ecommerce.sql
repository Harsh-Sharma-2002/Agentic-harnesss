-- ============================================================
-- Reset
-- ============================================================

DROP TABLE IF EXISTS payments CASCADE;
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS categories CASCADE;
DROP TABLE IF EXISTS customers CASCADE;


-- ============================================================
-- Customers
-- ============================================================

CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    state VARCHAR(50) NOT NULL,
    signup_date DATE NOT NULL
);


-- ============================================================
-- Categories
-- ============================================================

CREATE TABLE categories (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(100) UNIQUE NOT NULL
);


-- ============================================================
-- Products
-- ============================================================

CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    product_name VARCHAR(120) NOT NULL,
    category_id INTEGER NOT NULL,
    price NUMERIC(10, 2) NOT NULL,
    stock_quantity INTEGER NOT NULL,

    CONSTRAINT fk_product_category
        FOREIGN KEY (category_id)
        REFERENCES categories(category_id)
);


-- ============================================================
-- Orders
-- ============================================================

CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    order_date TIMESTAMP NOT NULL,
    status VARCHAR(30) NOT NULL,

    CONSTRAINT fk_order_customer
        FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id)
);


-- ============================================================
-- Order Items
-- ============================================================

CREATE TABLE order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price NUMERIC(10, 2) NOT NULL,

    CONSTRAINT fk_item_order
        FOREIGN KEY (order_id)
        REFERENCES orders(order_id),

    CONSTRAINT fk_item_product
        FOREIGN KEY (product_id)
        REFERENCES products(product_id)
);


-- ============================================================
-- Payments
-- ============================================================

CREATE TABLE payments (
    payment_id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL,
    payment_method VARCHAR(30) NOT NULL,
    amount NUMERIC(10, 2) NOT NULL,
    payment_status VARCHAR(30) NOT NULL,
    payment_date TIMESTAMP NOT NULL,

    CONSTRAINT fk_payment_order
        FOREIGN KEY (order_id)
        REFERENCES orders(order_id)
);


-- ============================================================
-- Categories
-- ============================================================

INSERT INTO categories (category_name)
VALUES
    ('Electronics'),
    ('Books'),
    ('Home'),
    ('Fitness'),
    ('Clothing'),
    ('Gaming');


-- ============================================================
-- Products
-- ============================================================

INSERT INTO products
    (product_name, category_id, price, stock_quantity)
VALUES
    ('Wireless Headphones', 1, 129.99, 80),
    ('Mechanical Keyboard', 1, 89.99, 60),
    ('USB-C Hub', 1, 49.99, 120),
    ('Smart Watch', 1, 199.99, 45),

    ('Distributed Systems', 2, 54.99, 40),
    ('Machine Learning', 2, 64.99, 35),
    ('Database Internals', 2, 59.99, 30),
    ('Operating Systems', 2, 49.99, 50),

    ('Coffee Maker', 3, 79.99, 45),
    ('Desk Lamp', 3, 39.99, 90),
    ('Office Chair', 3, 249.99, 25),

    ('Yoga Mat', 4, 29.99, 100),
    ('Adjustable Dumbbells', 4, 199.99, 25),
    ('Resistance Bands', 4, 24.99, 130),

    ('Running Shirt', 5, 34.99, 150),
    ('Hoodie', 5, 59.99, 75),
    ('Running Shoes', 5, 109.99, 60),

    ('Gaming Mouse', 6, 69.99, 80),
    ('Gaming Headset', 6, 119.99, 50),
    ('Controller', 6, 59.99, 70);


-- ============================================================
-- Generate 100 customers
-- ============================================================

INSERT INTO customers (
    first_name,
    last_name,
    email,
    state,
    signup_date
)
SELECT
    'Customer',
    gs::TEXT,
    'customer' || gs || '@example.com',

    (ARRAY[
        'Arizona',
        'California',
        'Texas',
        'Georgia',
        'Nevada',
        'Washington'
    ])[1 + floor(random() * 6)::INTEGER],

    DATE '2024-01-01'
        + floor(random() * 700)::INTEGER

FROM generate_series(1, 100) AS gs;


-- ============================================================
-- Generate 500 orders
-- ============================================================

INSERT INTO orders (
    customer_id,
    order_date,
    status
)
SELECT
    1 + floor(random() * 100)::INTEGER,

    TIMESTAMP '2024-01-01'
        + random() * INTERVAL '700 days',

    (ARRAY[
        'completed',
        'completed',
        'completed',
        'shipped',
        'cancelled'
    ])[1 + floor(random() * 5)::INTEGER]

FROM generate_series(1, 500);


-- ============================================================
-- Generate order items
--
-- Each order gets between 1 and 4 products.
-- ============================================================

INSERT INTO order_items (
    order_id,
    product_id,
    quantity,
    unit_price
)
SELECT
    o.order_id,
    p.product_id,
    1 + floor(random() * 3)::INTEGER,
    p.price

FROM orders o

CROSS JOIN LATERAL (

    SELECT product_id, price
    FROM products
    ORDER BY random()
    LIMIT (1 + floor(random() * 4)::INTEGER)

) p;


-- ============================================================
-- Generate payments
-- ============================================================

INSERT INTO payments (
    order_id,
    payment_method,
    amount,
    payment_status,
    payment_date
)
SELECT
    o.order_id,

    (ARRAY[
        'credit_card',
        'debit_card',
        'paypal'
    ])[1 + floor(random() * 3)::INTEGER],

    ROUND(
        SUM(oi.quantity * oi.unit_price),
        2
    ),

    CASE
        WHEN o.status = 'cancelled'
            THEN 'refunded'
        ELSE 'paid'
    END,

    o.order_date

FROM orders o

JOIN order_items oi
    ON oi.order_id = o.order_id

GROUP BY
    o.order_id,
    o.status,
    o.order_date;


-- ============================================================
-- Useful indexes
-- ============================================================

CREATE INDEX idx_orders_customer
    ON orders(customer_id);

CREATE INDEX idx_orders_date
    ON orders(order_date);

CREATE INDEX idx_order_items_order
    ON order_items(order_id);

CREATE INDEX idx_order_items_product
    ON order_items(product_id);

CREATE INDEX idx_products_category
    ON products(category_id);

CREATE INDEX idx_payments_order
    ON payments(order_id);