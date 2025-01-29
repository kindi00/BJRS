#!/bin/sh
CRYPT=$1
PASSWORD=$2
if [ -z $3 ]; then
    apt install uuid
    UUID=$(uuid)
    dd if=/dev/urandom bs=1 count=256 > $UUID.lek
else
    UUID=$3
fi
cryptsetup luksAddKey $CRYPT $UUID.lek
cat << "END" > luksunlockusb
#!/bin/sh
set -e
if [ ! -e /mnt ]; then
    mkdir -p /mnt
    sleep 3
fi
for usbpartition in /dev/disk/by-id/usb-*-part1; do
    usbdevice=$(readlink -f $usbpartition)
END
echo '    echo' $PASSWORD '| cryptsetup luksOpen $usbdevice mykey' >> luksunlockusb
cat << "END" >> luksunlockusb
    if mount /dev/mapper/mykey /mnt 2>/dev/null; then
        if [ -e /mnt/$CRYPTTAB_KEY.lek ]; then
            cat /mnt/$CRYPTTAB_KEY.lek
            umount /mnt
	    cryptsetup close mykey
            exit
        fi
        umount /mnt
    fi
done
END
chmod 755 ./luksunlockusb
cp ./luksunlockusb /bin/luksunlockusb
echo $UUID
