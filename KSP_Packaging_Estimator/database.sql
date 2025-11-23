CREATE TABLE variables (
    id SERIAL PRIMARY KEY,
    feature VARCHAR(255) UNIQUE NOT NULL,
    variable_name VARCHAR(255),
    multiplier DECIMAL(15, 5),
    updated_multiplier BOOLEAN DEFAULT FALSE,
    factory_set_constant DECIMAL(15, 5),
    customer_dependant_variable DECIMAL(15, 5),
    customer_variable DECIMAL(15, 5),
    cost_rate DECIMAL(15, 2),
    total DECIMAL(15, 5),
    equation_for_multiplier TEXT,
    equation_for_total TEXT
);

-- Index to speed up lookups by 'feature' as it’s often queried
CREATE INDEX idx_feature ON variables(feature);