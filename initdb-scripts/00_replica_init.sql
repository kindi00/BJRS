CREATE USER replicator WITH REPLICATION ENCRYPTED PASSWORD 'replicator046passwd';
SELECT pg_create_physical_replication_slot('replication_slot');