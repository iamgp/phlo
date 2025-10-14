-- Diagnostic queries for investigating DuckLake catalog lock contention
-- Run these against the PostgreSQL catalog database while partitions are hanging

-- 1. Show all active locks and waiting queries
SELECT
    a.pid,
    a.usename,
    a.state,
    a.wait_event_type,
    a.wait_event,
    now() - a.query_start AS query_duration,
    a.query,
    l.locktype,
    l.mode,
    l.granted
FROM pg_stat_activity a
LEFT JOIN pg_locks l ON a.pid = l.pid
WHERE a.datname = 'ducklake_catalog'
  AND a.state != 'idle'
ORDER BY query_duration DESC;

-- 2. Show blocking locks (who is blocking whom)
SELECT
    blocked_locks.pid AS blocked_pid,
    blocked_activity.usename AS blocked_user,
    blocking_locks.pid AS blocking_pid,
    blocking_activity.usename AS blocking_user,
    blocked_activity.query AS blocked_query,
    blocking_activity.query AS blocking_query,
    blocked_activity.application_name AS blocked_app
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks
    ON blocking_locks.locktype = blocked_locks.locktype
    AND blocking_locks.database IS NOT DISTINCT FROM blocked_locks.database
    AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
    AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
    AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
    AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
    AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
    AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
    AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
    AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
    AND blocking_locks.pid != blocked_locks.pid
JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted;

-- 3. Count of locks by type
SELECT locktype, mode, COUNT(*)
FROM pg_locks
GROUP BY locktype, mode
ORDER BY COUNT(*) DESC;

-- 4. Show long-running transactions
SELECT
    pid,
    now() - xact_start AS transaction_duration,
    query,
    state
FROM pg_stat_activity
WHERE xact_start IS NOT NULL
  AND datname = 'ducklake_catalog'
ORDER BY transaction_duration DESC;

-- 5. Check DuckLake-specific tables for concurrent access
SELECT
    schemaname,
    tablename,
    n_tup_ins AS inserts,
    n_tup_upd AS updates,
    n_tup_del AS deletes,
    n_live_tup AS live_tuples,
    n_dead_tup AS dead_tuples,
    last_vacuum,
    last_autovacuum
FROM pg_stat_user_tables
WHERE schemaname LIKE 'main_%'
ORDER BY n_tup_ins DESC;
