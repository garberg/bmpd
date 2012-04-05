--
-- period.sql
--   SQL install script for the PERIOD data type.
--
-- Portions Copyright (c) 2007-2008, Jeff Davis <jeff@j-davis.com>
--

CREATE TYPE period;

CREATE OR REPLACE FUNCTION period_in(cstring) RETURNS period LANGUAGE C IMMUTABLE STRICT 
  AS '$libdir/period','period_in';

CREATE OR REPLACE FUNCTION period_out(period) RETURNS cstring LANGUAGE C IMMUTABLE STRICT 
  AS '$libdir/period','period_out';

CREATE TYPE period(
  input = period_in,
  output = period_out,
  internallength = 16,
  alignment = double
);


--
-- INTERVAL
--

CREATE OR REPLACE FUNCTION length(period) RETURNS INTERVAL LANGUAGE C IMMUTABLE STRICT 
  AS '$libdir/period','length_period';

CREATE OR REPLACE FUNCTION period_offset(period, timestamptz) RETURNS INTERVAL LANGUAGE C IMMUTABLE STRICT 
  AS '$libdir/period','period_offset_period_timestamptz';

CREATE OR REPLACE FUNCTION period_offset_sec(period, timestamptz) RETURNS BIGINT LANGUAGE C IMMUTABLE STRICT
  AS '$libdir/period','period_offset_sec_period_timestamptz';

-- 
-- TIMESTAMPTZ
--

CREATE OR REPLACE FUNCTION first(period) RETURNS TIMESTAMPTZ LANGUAGE C IMMUTABLE STRICT 
  AS '$libdir/period','first_period';

CREATE OR REPLACE FUNCTION last(period) RETURNS TIMESTAMPTZ LANGUAGE C IMMUTABLE STRICT 
  AS '$libdir/period','last_period';

CREATE OR REPLACE FUNCTION prior(period) RETURNS TIMESTAMPTZ LANGUAGE C IMMUTABLE STRICT 
  AS '$libdir/period','prior_period';

CREATE OR REPLACE FUNCTION next(period) RETURNS TIMESTAMPTZ LANGUAGE C IMMUTABLE STRICT 
  AS '$libdir/period','next_period';

--
-- BOOLEAN
--

CREATE OR REPLACE FUNCTION contains(period,TIMESTAMPTZ) RETURNS BOOLEAN LANGUAGE C IMMUTABLE STRICT 
  AS '$libdir/period','contains_period_timestamptz';

CREATE OR REPLACE FUNCTION contains(period,period) RETURNS BOOLEAN LANGUAGE C IMMUTABLE STRICT 
  AS '$libdir/period','contains_period_period';

CREATE OR REPLACE FUNCTION contained_by(TIMESTAMPTZ,period) RETURNS BOOLEAN LANGUAGE C IMMUTABLE STRICT 
  AS '$libdir/period','contained_by_timestamptz_period';

CREATE OR REPLACE FUNCTION contained_by(period,period) RETURNS BOOLEAN LANGUAGE C IMMUTABLE STRICT 
  AS '$libdir/period','contained_by_period_period';

CREATE OR REPLACE FUNCTION adjacent(period,period) RETURNS BOOLEAN LANGUAGE C IMMUTABLE STRICT 
  AS '$libdir/period','adjacent_period_period';

CREATE OR REPLACE FUNCTION overlaps(period,period) RETURNS BOOLEAN LANGUAGE C IMMUTABLE STRICT 
  AS '$libdir/period','overlaps_period_period';

CREATE OR REPLACE FUNCTION overleft(period,period) RETURNS BOOLEAN LANGUAGE C IMMUTABLE STRICT 
  AS '$libdir/period','overleft_period_period';

CREATE OR REPLACE FUNCTION overright(period,period) RETURNS BOOLEAN LANGUAGE C IMMUTABLE STRICT 
  AS '$libdir/period','overright_period_period';

CREATE OR REPLACE FUNCTION is_empty(period) RETURNS BOOLEAN LANGUAGE C IMMUTABLE STRICT 
  AS '$libdir/period','is_empty_period';

CREATE OR REPLACE FUNCTION equals(period,period) RETURNS BOOLEAN LANGUAGE C IMMUTABLE STRICT 
  AS '$libdir/period','equals_period_period';

CREATE OR REPLACE FUNCTION nequals(period,period) RETURNS BOOLEAN LANGUAGE C IMMUTABLE STRICT 
  AS '$libdir/period','nequals_period_period';

CREATE OR REPLACE FUNCTION before(period,period) RETURNS BOOLEAN LANGUAGE C IMMUTABLE STRICT 
  AS '$libdir/period','before_period_period';

CREATE OR REPLACE FUNCTION after(period,period) RETURNS BOOLEAN LANGUAGE C IMMUTABLE STRICT 
  AS '$libdir/period','after_period_period';

--
-- period
--

CREATE OR REPLACE FUNCTION empty_period() RETURNS period LANGUAGE C IMMUTABLE STRICT
  AS '$libdir/period','empty_period';

CREATE OR REPLACE FUNCTION period_intersect(period,period) RETURNS period LANGUAGE C IMMUTABLE STRICT
  AS '$libdir/period','intersect_period_period';

CREATE OR REPLACE FUNCTION period_union(period,period) RETURNS period LANGUAGE C IMMUTABLE STRICT
  AS '$libdir/period','union_period_period';

CREATE OR REPLACE FUNCTION period(TIMESTAMPTZ) RETURNS period LANGUAGE C IMMUTABLE STRICT
  AS '$libdir/period','period_timestamptz';

CREATE OR REPLACE FUNCTION period(TIMESTAMPTZ,TIMESTAMPTZ) RETURNS period LANGUAGE C IMMUTABLE STRICT
  AS '$libdir/period','period_co_timestamptz_timestamptz';

CREATE OR REPLACE FUNCTION period_oo(TIMESTAMPTZ,TIMESTAMPTZ) RETURNS period LANGUAGE C IMMUTABLE STRICT
  AS '$libdir/period','period_oo_timestamptz_timestamptz';

CREATE OR REPLACE FUNCTION period_oc(TIMESTAMPTZ,TIMESTAMPTZ) RETURNS period LANGUAGE C IMMUTABLE STRICT
  AS '$libdir/period','period_oc_timestamptz_timestamptz';

CREATE OR REPLACE FUNCTION period_co(TIMESTAMPTZ,TIMESTAMPTZ) RETURNS period LANGUAGE C IMMUTABLE STRICT
  AS '$libdir/period','period_co_timestamptz_timestamptz';

CREATE OR REPLACE FUNCTION period_cc(TIMESTAMPTZ,TIMESTAMPTZ) RETURNS period LANGUAGE C IMMUTABLE STRICT
  AS '$libdir/period','period_cc_timestamptz_timestamptz';

CREATE OR REPLACE FUNCTION minus(period,period) RETURNS period LANGUAGE C IMMUTABLE STRICT
  AS '$libdir/period','minus_period_period';

--
-- GiST Support
--

CREATE OR REPLACE FUNCTION gist_period_consistent(internal, period, int4) RETURNS BOOLEAN LANGUAGE C
  AS '$libdir/period';

CREATE OR REPLACE FUNCTION gist_period_union(internal, internal) RETURNS period LANGUAGE C
  AS '$libdir/period';

CREATE OR REPLACE FUNCTION gist_period_compress(internal) RETURNS INTERNAL LANGUAGE C
  AS '$libdir/period';

CREATE OR REPLACE FUNCTION gist_period_decompress(internal) RETURNS INTERNAL LANGUAGE C
  AS '$libdir/period';

CREATE OR REPLACE FUNCTION gist_period_penalty(internal, internal, internal) RETURNS INTERNAL LANGUAGE C
  AS '$libdir/period';

CREATE OR REPLACE FUNCTION gist_period_picksplit(internal, internal) RETURNS INTERNAL LANGUAGE C
  AS '$libdir/period';

CREATE OR REPLACE FUNCTION gist_period_same(period, period, internal) RETURNS INTERNAL LANGUAGE C
  AS '$libdir/period';

--
-- operators
--

-- equals
CREATE OPERATOR = (
  PROCEDURE = equals,
  LEFTARG   = period,
  RIGHTARG  = period,
  NEGATOR   = !=,
  RESTRICT  = eqsel
);

CREATE OPERATOR != (
  PROCEDURE = nequals,
  LEFTARG   = period,
  RIGHTARG  = period,
  NEGATOR   = =,
  RESTRICT  = neqsel
);

-- minus
CREATE OPERATOR - (
  PROCEDURE = minus,
  LEFTARG   = period,
  RIGHTARG  = period
);

-- plus
CREATE OPERATOR + (
  PROCEDURE = period_union,
  LEFTARG   = period,
  RIGHTARG  = period
);

-- contains (period,period)
CREATE OPERATOR @> (
  PROCEDURE = contains,
  LEFTARG   = period,
  RIGHTARG  = period,
  COMMUTATOR= <@,
  RESTRICT  = contsel 
);

-- contains (period,TIMESTAMPTZ)
CREATE OPERATOR @> (
  PROCEDURE = contains,
  LEFTARG   = period,
  RIGHTARG  = TIMESTAMPTZ,
  COMMUTATOR= <@,
  RESTRICT  = contsel
);

-- contained_by (period,period)
CREATE OPERATOR <@ (
  PROCEDURE = contained_by,
  LEFTARG   = period,
  RIGHTARG  = period,
  COMMUTATOR= @>,
  RESTRICT  = contsel
);

-- contained_by (TIMESTAMPTZ,period)
CREATE OPERATOR <@ (
  PROCEDURE = contained_by,
  LEFTARG   = TIMESTAMPTZ,
  RIGHTARG  = period,
  COMMUTATOR= @>,
  RESTRICT  = contsel
);

-- alias for contains (period,period)
CREATE OPERATOR ~ (
  PROCEDURE = contains,
  LEFTARG   = period,
  RIGHTARG  = period,
  COMMUTATOR= @,
  RESTRICT  = contsel
);

-- alias for contains (period,TIMESTAMPTZ)
CREATE OPERATOR ~ (
  PROCEDURE = contains,
  LEFTARG   = period,
  RIGHTARG  = TIMESTAMPTZ,
  COMMUTATOR= @,
  RESTRICT  = contsel
);

-- alias for contained_by (period,period)
CREATE OPERATOR @ (
  PROCEDURE = contained_by,
  LEFTARG   = period,
  RIGHTARG  = period,
  COMMUTATOR= ~,
  RESTRICT  = contsel
);

-- alias for contained_by (period,TIMESTAMPTZ)
CREATE OPERATOR @ (
  PROCEDURE = contained_by,
  LEFTARG   = TIMESTAMPTZ,
  RIGHTARG  = period,
  COMMUTATOR= ~,
  RESTRICT  = contsel
);

-- overlaps
CREATE OPERATOR && (
  PROCEDURE = overlaps,
  LEFTARG   = period,
  RIGHTARG  = period,
  RESTRICT  = areasel,
  COMMUTATOR= &&
);

-- strictly before
CREATE OPERATOR << (
  PROCEDURE = before,
  LEFTARG   = period,
  RIGHTARG  = period,
  COMMUTATOR= >>,
  RESTRICT  = areasel
);

-- strictly after
CREATE OPERATOR >> (
  PROCEDURE = after,
  LEFTARG   = period,
  RIGHTARG  = period,
  COMMUTATOR= <<,
  RESTRICT  = areasel
);

-- A.last <= B.last
CREATE OPERATOR &< (
  PROCEDURE = overleft,
  LEFTARG   = period,
  RIGHTARG  = period,
  RESTRICT  = areasel
);

-- A.first >= B.first
CREATE OPERATOR &> (
  PROCEDURE = overright,
  LEFTARG   = period,
  RIGHTARG  = period,
  RESTRICT  = areasel
);

CREATE OPERATOR CLASS gist_period_ops
  DEFAULT FOR TYPE period USING gist AS
    OPERATOR  1    <<,  -- strictly before
    OPERATOR  2    &<,  -- overlaps or left of
    OPERATOR  3    &&,  -- overlaps
    OPERATOR  4    &>,  -- overlaps or right of
    OPERATOR  5    >>,  -- strictly after
    OPERATOR  6    =,   -- equal
    OPERATOR  7    @>,  -- contains
    OPERATOR  8    <@,  -- contained by
    OPERATOR 17    ~,   -- alias for contains
    OPERATOR 18    @,   -- alias for contained by
    OPERATOR 27    @>(period,TIMESTAMPTZ),
    OPERATOR 28    <@(TIMESTAMPTZ,period),
    FUNCTION  1    gist_period_consistent(internal, period, int4),
    FUNCTION  2    gist_period_union(internal, internal),
    FUNCTION  3    gist_period_compress(internal),
    FUNCTION  4    gist_period_decompress(internal),
    FUNCTION  5    gist_period_penalty(internal, internal, internal),
    FUNCTION  6    gist_period_picksplit(internal, internal),
    FUNCTION  7    gist_period_same(period, period, internal);

