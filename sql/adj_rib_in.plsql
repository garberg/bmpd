--
--
--
DROP TABLE IF EXISTS adj_rib_in;
CREATE TABLE adj_rib_in (
	id SERIAL PRIMARY KEY,
	valid period NOT NULL,
	bmp_src inet NOT NULL,
	neighbor_addr inet NOT NULL,
	neighbor_as integer NOT NULL,
	next_hop inet NOT NULL,
	lpref integer NOT NULL,
	med integer NOT NULL,
	prefix cidr NOT NULL,
	aspath integer[],
	communities TEXT[]
);

CREATE INDEX valid_idx ON adj_rib_in USING GiST ();

CREATE UNIQUE INDEX  ON adj_rib_in (valid, bmp_source, neighbor_addr, prefix);

COMMENT ON TABLE adj_rib_in IS '';
COMMENT ON COLUMN adj_rib_in.id IS '';
COMMENT ON COLUMN adj_rib_in.valid IS 'The period for which the data was valid.';
COMMENT ON COLUMN adj_rib_in.bmp_src IS 'Source host for BMP packet.';
COMMENT ON COLUMN adj_rib_in.neighbor_addr IS 'Address of neighbor from which the update was received.';
COMMENT ON COLUMN adj_rib_in.neighbor_as IS 'AS of the neighbor from which the update was received.';
COMMENT ON COLUMN adj_rib_in.next_hop IS 'Next-hop advertised by the neighbor.';
COMMENT ON COLUMN adj_rib_in.lpref IS 'Local preference of entry.';
COMMENT ON COLUMN adj_rib_in.med IS 'MED of entry';
COMMENT ON COLUMN adj_rib_in.prefix IS 'Announced prefix.';
COMMENT ON COLUMN adj_rib_in.aspath IS 'AS path.';
COMMENT ON COLUMN adj_rib_in.communities IS 'Communities the prefix is tagged with.';

--CREATE TABLE raw_log (
--	id SERIAL PRIMARY KEY,
--	bmp_src inet NOT NULL,
--	bgp_data bytea
--);
