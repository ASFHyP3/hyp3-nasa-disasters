#!/bin/bash
set -ex

apt update -y
apt upgrade -y
apt autoremove -y

cp /opt/arcgis/server/framework/etc/scripts/arcgisserver.service /etc/systemd/system/arcgisserver.service
chmod 600 /etc/systemd/system/arcgisserver.service
systemctl enable arcgisserver.service
systemctl start arcgisserver.service

sed -i 's/8080/6080/' /etc/iptables/rules.v4
sed -i 's/8443/6443/' /etc/iptables/rules.v4
