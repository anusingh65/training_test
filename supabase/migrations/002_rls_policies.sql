-- Row Level Security Policies

-- Enable RLS on all tables
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE drugs ENABLE ROW LEVEL SECURITY;
ALTER TABLE custody_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE verification_scans ENABLE ROW LEVEL SECURITY;
ALTER TABLE flagged_reports ENABLE ROW LEVEL SECURITY;

-- Helper: check user role
CREATE OR REPLACE FUNCTION auth_role()
RETURNS user_role AS $$
  SELECT role FROM profiles WHERE id = auth.uid()
$$ LANGUAGE sql SECURITY DEFINER STABLE;

-- Profiles
CREATE POLICY "Users can read own profile"
  ON profiles FOR SELECT USING (id = auth.uid());

CREATE POLICY "Admins can read all profiles"
  ON profiles FOR SELECT USING (auth_role() = 'admin');

CREATE POLICY "Users can update own profile"
  ON profiles FOR UPDATE USING (id = auth.uid());

CREATE POLICY "Users can insert own profile"
  ON profiles FOR INSERT WITH CHECK (id = auth.uid());

-- Drugs
CREATE POLICY "Anyone can read drugs"
  ON drugs FOR SELECT USING (true);

CREATE POLICY "Manufacturers can insert drugs"
  ON drugs FOR INSERT WITH CHECK (
    auth_role() IN ('manufacturer', 'admin')
  );

CREATE POLICY "Admins can update drugs"
  ON drugs FOR UPDATE USING (auth_role() = 'admin');

-- Custody Events
CREATE POLICY "Anyone can read custody events"
  ON custody_events FOR SELECT USING (true);

CREATE POLICY "Authorized roles can insert custody events"
  ON custody_events FOR INSERT WITH CHECK (
    auth_role() IN ('manufacturer', 'commuter', 'admin')
  );

-- Verification Scans
CREATE POLICY "Consumers can insert own scans"
  ON verification_scans FOR INSERT WITH CHECK (
    scanner_id = auth.uid()
  );

CREATE POLICY "Users can read own scans"
  ON verification_scans FOR SELECT USING (
    scanner_id = auth.uid() OR auth_role() = 'admin'
  );

CREATE POLICY "Admins can read all scans"
  ON verification_scans FOR SELECT USING (auth_role() = 'admin');

-- Flagged Reports
CREATE POLICY "Anyone can insert flagged reports"
  ON flagged_reports FOR INSERT WITH CHECK (true);

CREATE POLICY "Anyone can read flagged reports"
  ON flagged_reports FOR SELECT USING (true);

CREATE POLICY "Admins can update flagged reports"
  ON flagged_reports FOR UPDATE USING (auth_role() = 'admin');
