-- ==============================================================================
-- Child Safety Platform — Database Initialization
-- ==============================================================================
-- This script runs on first PostgreSQL container startup.
-- It enables required extensions.
-- ==============================================================================

-- Enable PostGIS for geospatial queries (SOS locations, missing children, etc.)
CREATE EXTENSION IF NOT EXISTS postgis;

-- Enable pgvector for vector similarity search (case embeddings, image search)
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable uuid-ossp for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pgcrypto for encryption functions
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Verify extensions
SELECT extname, extversion FROM pg_extension WHERE extname IN ('postgis', 'vector', 'uuid-ossp', 'pgcrypto');
