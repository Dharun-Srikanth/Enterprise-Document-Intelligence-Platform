-- Enterprise Document Intelligence Platform - Database Schema
-- Generated DDL for PostgreSQL

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Documents table
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR(500) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    mime_type VARCHAR(100),
    doc_category VARCHAR(50),
    doc_category_secondary VARCHAR(50),
    category_confidence FLOAT,
    raw_text TEXT,
    clean_text TEXT,
    structure_metadata JSONB,
    ocr_confidence FLOAT,
    processing_status VARCHAR(20) DEFAULT 'pending',
    processing_error TEXT,
    file_path VARCHAR(1000),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Entities extracted from documents
CREATE TABLE IF NOT EXISTS entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    entity_type VARCHAR(50) NOT NULL,
    entity_value TEXT NOT NULL,
    normalized_value TEXT,
    confidence FLOAT,
    start_offset INT,
    end_offset INT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Relationships between entities
CREATE TABLE IF NOT EXISTS entity_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    source_entity_id UUID REFERENCES entities(id) ON DELETE CASCADE,
    target_entity_id UUID REFERENCES entities(id) ON DELETE CASCADE,
    relationship_type VARCHAR(100),
    confidence FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tear-down component classifications
CREATE TABLE IF NOT EXISTS components (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    component_type VARCHAR(100) NOT NULL,
    component_confidence FLOAT,
    material VARCHAR(100),
    material_confidence FLOAT,
    estimated_cost_low DECIMAL(12,2),
    estimated_cost_high DECIMAL(12,2),
    estimated_cost_mid DECIMAL(12,2),
    carbon_footprint_kg_co2e DECIMAL(10,4),
    emission_factor_source VARCHAR(200),
    overall_confidence FLOAT,
    is_flagged BOOLEAN DEFAULT FALSE,
    flag_reason TEXT,
    classification_metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Benchmark reference data
CREATE TABLE IF NOT EXISTS benchmark_data (
    id SERIAL PRIMARY KEY,
    component_type VARCHAR(100) NOT NULL,
    material VARCHAR(100) NOT NULL,
    cost_low DECIMAL(12,2),
    cost_high DECIMAL(12,2),
    cost_unit VARCHAR(20) DEFAULT 'USD',
    carbon_footprint_kg_co2e DECIMAL(10,4),
    emission_factor_source VARCHAR(200),
    notes TEXT
);

-- Document chunks for vector store tracking
CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INT,
    chunk_text TEXT NOT NULL,
    chunk_metadata JSONB,
    vector_id VARCHAR(200),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Query audit logs
CREATE TABLE IF NOT EXISTS query_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_type VARCHAR(20) NOT NULL,
    user_query TEXT NOT NULL,
    generated_sql TEXT,
    result_summary TEXT,
    sources JSONB,
    confidence FLOAT,
    error TEXT,
    execution_time_ms INT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(processing_status);
CREATE INDEX IF NOT EXISTS idx_documents_file_type ON documents(file_type);
CREATE INDEX IF NOT EXISTS idx_entities_document_id ON entities(document_id);
CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_entity_relationships_document_id ON entity_relationships(document_id);
CREATE INDEX IF NOT EXISTS idx_components_document_id ON components(document_id);
CREATE INDEX IF NOT EXISTS idx_components_type ON components(component_type);
CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id ON document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_query_logs_type ON query_logs(query_type);
