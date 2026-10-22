-- PharmaChain Database Schema

-- Enums
CREATE TYPE user_role AS ENUM ('admin', 'manufacturer', 'commuter', 'consumer');
CREATE TYPE verification_status AS ENUM ('verified', 'suspicious', 'counterfeit', 'pending');
CREATE TYPE alert_severity AS ENUM ('low', 'medium', 'high', 'critical');
CREATE TYPE report_status AS ENUM ('pending', 'investigating', 'confirmed', 'dismissed');

-- Profiles
CREATE TABLE profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email TEXT NOT NULL,
  full_name TEXT,
  role user_role NOT NULL DEFAULT 'consumer',
  organization TEXT,
  wallet_address TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Drugs
CREATE TABLE drugs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  drug_id TEXT UNIQUE NOT NULL,
  batch_id TEXT NOT NULL,
  name TEXT NOT NULL,
  manufacturer TEXT NOT NULL,
  manufacturer_id UUID REFERENCES profiles(id),
  manufacture_date DATE NOT NULL,
  expiry_date DATE NOT NULL,
  metadata_hash TEXT NOT NULL,
  qr_hash TEXT NOT NULL,
  ipfs_cid TEXT,
  blockchain_tx_hash TEXT,
  contract_address TEXT,
  status verification_status NOT NULL DEFAULT 'pending',
  flagged BOOLEAN NOT NULL DEFAULT false,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Custody Events
CREATE TABLE custody_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  drug_id TEXT NOT NULL REFERENCES drugs(drug_id),
  from_entity TEXT,
  from_address TEXT,
  to_entity TEXT,
  to_address TEXT,
  event_type TEXT NOT NULL, -- manufactured, shipped, received, delivered
  location TEXT,
  latitude DOUBLE PRECISION,
  longitude DOUBLE PRECISION,
  blockchain_tx_hash TEXT,
  timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Verification Scans
CREATE TABLE verification_scans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  drug_id TEXT NOT NULL REFERENCES drugs(drug_id),
  scanner_id UUID REFERENCES profiles(id),
  scanner_role user_role,
  location TEXT,
  latitude DOUBLE PRECISION,
  longitude DOUBLE PRECISION,
  result verification_status NOT NULL,
  risk_score DOUBLE PRECISION,
  hash_matched BOOLEAN NOT NULL DEFAULT true,
  blockchain_verified BOOLEAN NOT NULL DEFAULT false,
  scanned_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Flagged Reports
CREATE TABLE flagged_reports (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  drug_id TEXT NOT NULL REFERENCES drugs(drug_id),
  reporter_id UUID REFERENCES profiles(id),
  reason TEXT NOT NULL,
  description TEXT,
  severity alert_severity NOT NULL DEFAULT 'medium',
  status report_status NOT NULL DEFAULT 'pending',
  location TEXT,
  latitude DOUBLE PRECISION,
  longitude DOUBLE PRECISION,
  resolved_by UUID REFERENCES profiles(id),
  resolved_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indexes
CREATE INDEX idx_drugs_drug_id ON drugs(drug_id);
CREATE INDEX idx_drugs_batch_id ON drugs(batch_id);
CREATE INDEX idx_drugs_status ON drugs(status);
CREATE INDEX idx_custody_drug_id ON custody_events(drug_id);
CREATE INDEX idx_custody_timestamp ON custody_events(timestamp);
CREATE INDEX idx_scans_drug_id ON verification_scans(drug_id);
CREATE INDEX idx_scans_scanned_at ON verification_scans(scanned_at);
CREATE INDEX idx_flagged_drug_id ON flagged_reports(drug_id);
CREATE INDEX idx_flagged_status ON flagged_reports(status);
CREATE INDEX idx_flagged_severity ON flagged_reports(severity);

-- Enable Realtime
ALTER PUBLICATION supabase_realtime ADD TABLE custody_events;
ALTER PUBLICATION supabase_realtime ADD TABLE verification_scans;
ALTER PUBLICATION supabase_realtime ADD TABLE flagged_reports;

-- Updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER profiles_updated_at BEFORE UPDATE ON profiles FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER drugs_updated_at BEFORE UPDATE ON drugs FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER flagged_updated_at BEFORE UPDATE ON flagged_reports FOR EACH ROW EXECUTE FUNCTION update_updated_at();
