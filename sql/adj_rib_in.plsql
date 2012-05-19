--
--
--


CREATE TYPE origin_type AS ENUM ('IGP', 'EGP', 'INCOMPLETE');
COMMENT ON TYPE origin_type IS 'BGP origin path attribute.';

DROP TABLE IF EXISTS adj_rib_in;
CREATE TABLE adj_rib_in (
	id SERIAL PRIMARY KEY,
	valid_from TIMESTAMP WITH TIME ZONE NOT NULL,
	valid_to TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT 'infinity',
	bmp_src inet NOT NULL,
	neighbor_addr inet NOT NULL,
	neighbor_as integer NOT NULL,
	next_hop inet NOT NULL,
    origin origin_type NOT NULL,
	lpref integer,
	med integer,
	prefix cidr NOT NULL,
	aspath integer[] NOT NULL,
	communities TEXT[]
);

COMMENT ON TABLE adj_rib_in IS 'Routing information base.';
COMMENT ON COLUMN adj_rib_in.id IS 'Unique ID for each entry.';
COMMENT ON COLUMN adj_rib_in.valid IS 'The period for which the data was valid.';
COMMENT ON COLUMN adj_rib_in.bmp_src IS 'Source host for BMP packet.';
COMMENT ON COLUMN adj_rib_in.neighbor_addr IS 'Address of neighbor from which the update was received.';
COMMENT ON COLUMN adj_rib_in.neighbor_as IS 'AS of the neighbor from which the update was received.';
COMMENT ON COLUMN adj_rib_in.next_hop IS 'Next-hop advertised by the neighbor.';
COMMENT ON COLUMN adj_rib_in.origin IS 'Origin of update.';
COMMENT ON COLUMN adj_rib_in.lpref IS 'Local preference of entry.';
COMMENT ON COLUMN adj_rib_in.med IS 'MED of entry';
COMMENT ON COLUMN adj_rib_in.prefix IS 'Announced prefix.';
COMMENT ON COLUMN adj_rib_in.aspath IS 'AS path.';
COMMENT ON COLUMN adj_rib_in.communities IS 'Communities the prefix is tagged with.';

--CREATE UNIQUE INDEX valid__bmp_src__neighbor_addr__prefix ON adj_rib_in (valid, bmp_src, neighbor_addr, prefix);

CREATE INDEX bmp_src__neighbor_addr__prefix__valid ON adj_rib_in (bmp_src, neighbor_addr, prefix);
CREATE INDEX valid_from__valid_to ON adj_rib_in (valid_from, valid_to);
CREATE INDEX valid_idx ON adj_rib_in USING gist (valid);


DROP TABLE IF EXISTS raw_log;
CREATE TABLE raw_log (
	id SERIAL PRIMARY KEY,
    ts TIMESTAMP,
	bmp_src inet NOT NULL,
    bgp_src inet NOT NULL,
	bgp_data bytea NOT NULL
);

COMMENT ON TABLE raw_log IS 'A log of raw BGP updates.';
