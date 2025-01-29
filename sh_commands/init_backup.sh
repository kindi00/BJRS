if [ -z "$( ls -A $PRIDIR )" ]; then
    DIR=$PRIDIR
    RMDIR=$SECDIR
else
    DIR=$SECDIR
    RMDIR=$PRIDIR
fi
echo "DIR:" $DIR
echo "RMDIR:" $RMDIR
until pg_basebackup --pgdata=$DIR -R --slot=replication_slot --host=$IP --port=5432
do
echo 'Waiting for primary to connect...'
sleep 1s
done
echo 'Cleaning old files...'
rm -r $RMDIR/*
echo 'Starting replica...'
chmod 0700 $DIR
postgres -D $DIR