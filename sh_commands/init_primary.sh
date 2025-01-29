if [ -z "$( ls -A $PRIDIR )" ]; then
    DIR=$SECDIR
    RMDIR=$PRIDIR
else
    DIR=$PRIDIR
    RMDIR=$SECDIR
fi
echo 'DIR:' $DIR
postgres -c wal_level=replica -c hot_standby=on -c max_wal_senders=10 -c max_replication_slots=10 -c hot_standby_feedback=on -D $DIR