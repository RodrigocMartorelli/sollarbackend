-- Inventory Table Schema for Solla Solar

CREATE TABLE IF NOT EXISTS inventory (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    brand VARCHAR(150) NOT NULL,
    quantity NUMERIC(12, 2) NOT NULL CHECK (quantity >= 0),
    unit VARCHAR(10) NOT NULL DEFAULT 'un',
    type VARCHAR(100) NOT NULL,
    observations TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_inventory_type ON inventory(type);
CREATE INDEX IF NOT EXISTS idx_inventory_name ON inventory(name);
CREATE INDEX IF NOT EXISTS idx_inventory_brand ON inventory(brand);
CREATE INDEX IF NOT EXISTS idx_inventory_created_at ON inventory(created_at);

-- Create trigger to auto-update updated_at
CREATE OR REPLACE FUNCTION update_inventory_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_inventory_updated_at_trigger
BEFORE UPDATE ON inventory
FOR EACH ROW
EXECUTE FUNCTION update_inventory_updated_at();

-- Insert initial data (optional)
INSERT INTO inventory (name, brand, quantity, unit, type, observations)
VALUES 
    ('Cabo Solar 4mm²', 'Siemens', 150.5, 'm', 'Cabo', 'Estoque principal'),
    ('Placa Solar 400W', 'Canadian Solar', 25, 'un', 'Placa Solar', NULL),
    ('Inversor Solar 5kW', 'SMA', 8, 'un', 'Inversor', 'Garantia 10 anos'),
    ('Estrutura Alumínio 10x10', 'Telcosol', 45.0, 'm', 'Estrutura', NULL),
    ('Conector MC4', 'Phoenix Contact', 200, 'un', 'Conector', 'Compatível com padrão'),
    ('Disjuntor DC 32A', 'Schneider Electric', 15, 'un', 'Proteção', NULL),
    ('Caixa String DC', 'ABB', 12, 'un', 'Caixa', 'Para 3 strings máximo'),
    ('Aterramento em Cobre', 'Nexans', 300.0, 'm', 'Aterramento', 'Bitola 6mm²'),
    ('Fusível Solar 20A', 'Littelfuse', 100, 'un', 'Proteção', NULL),
    ('Tubo Eletroduto 20mm', 'Tigre', 500.0, 'm', 'Acessório', NULL)
ON CONFLICT (name) DO NOTHING;
