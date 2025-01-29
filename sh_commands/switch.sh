if [ -z "$( ls -A $PRIDIR )" ]; then
    DIR=$SECDIR
    RMDIR=$PRIDIR
else
    DIR=$PRIDIR
    RMDIR=$SECDIR
fi
echo "DIR:" $DIR
echo "RMDIR:" $RMDIR
echo 'Adding second server...'
echo "host replication replicator $IP/32 md5" >> $DIR/pg_hba.conf
psql -U $POSTGRES_USER -d $POSTGRES_DB -c "select * from pg_promote(); select pg_create_physical_replication_slot('replication_slot');"
echo 'Done'