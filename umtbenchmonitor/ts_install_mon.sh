#!/bin/bash

if [ $# -eq 0 ]
  then
    echo "No arguments supplied"
    echo "./ts_install_mon.sh <mon_ip> <mon_port> <slot_ids_by_commas> <station> <mon_wip> <mon_wport>"
    exit 1
fi

mon_ip=$1
mon_port=$2
SLOT=(${3//,/ })
station=$4
mon_wip=$5
mon_wport=$6

#UPDATE MON CONF FILES
awk '{gsub(a,b);print}' a='{MON_IP}' b=$mon_ip tscore1/src/frwk_config/frwk_mon.conf  > temp_frwk_mon.conf
awk '{gsub(a,b);print}' a='6252' b=$mon_port temp_frwk_mon.conf  > tscore1/src/frwk_config/frwk_mon.conf
cp tscore1/src/frwk_config/frwk_mon.conf temp_frwk_mon.conf

awk '{gsub(a,b);print}' a='{SLOT_ID}' b=${SLOT[0]} temp_frwk_mon.conf  > tscore1/src/frwk_config/frwk_mon.conf
awk '{gsub(a,b);print}' a='{SLOT_ID}' b=${SLOT[1]} temp_frwk_mon.conf  > tscore2/src/frwk_config/frwk_mon.conf
awk '{gsub(a,b);print}' a='{SLOT_ID}' b=${SLOT[2]} temp_frwk_mon.conf  > tscore3/src/frwk_config/frwk_mon.conf
awk '{gsub(a,b);print}' a='{SLOT_ID}' b=${SLOT[3]} temp_frwk_mon.conf  > tscore4/src/frwk_config/frwk_mon.conf

#UPDATE UMT BENCH
awk '{gsub(a,b);print}' a='{STATION}' b=$station umtbenchmonitor/config.properties  > tempconfig.properties
awk '{gsub(a,b);print}' a='{MONWEBIP}' b=$mon_wip tempconfig.properties  > umtbenchmonitor/config.properties
awk '{gsub(a,b);print}' a='{MONWEBPORT}' b=$mon_wport umtbenchmonitor/config.properties  > tempconfig.properties
awk '{gsub(a,b);print}' a='{MONPORT}' b=$mon_port tempconfig.properties  > umtbenchmonitor/config.properties

rm temp_frwk_mon.conf
rm tempconfig.properties

# Need arguments:
# mon_ip, mon_port, slot_ids, station, mon_wip, mon_wport
