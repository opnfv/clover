#!/bin/bash

TITLE="System Information for $HOSTNAME"
RIGHT_NOW=$(date +"%x %r %Z")
TIME_STAMP="Updated on $RIGHT_NOW by $USER"

BONO_SIP_PROXY_IP=$1
ELLIS_IP=$2
BASIC=$3

para1=0
para2=0
if [[ -n "$BONO_SIP_PROXY_IP" ]];then 
   para1=1
else
   echo "ERROR: Missing External Loadbalancer IP for Bono"
fi
if [[ -n "$ELLIS_IP" ]];then
   para2=1
else
   echo "ERROR: Missing External Loadbalancer IP for Ellis"
fi

if [ "$para1" -eq "0" ];then
   echo "";echo "USAGE: $0 <BONO_SIP_PROXY_IP> <ELLIS_IP>";echo ""
   exit
fi
if [ "$para2" -eq "0" ];then
   echo "";echo "USAGE: $0 <BONO_SIP_PROXY_IP> <ELLIS_IP>";echo ""
   exit
fi


if [[ $para1 == 1 && $para2 == 1 ]];then 
   if [ "$BASIC" == "basic" ];then
      docker exec -it live-test bash -c "source /etc/profile.d/rvm.sh && cd /opt/clearwater-live-test && rake test[default.svc.cluster.local] PROXY=$BONO_SIP_PROXY_IP ELLIS=$ELLIS_IP SIGNUP_CODE=\"secret\" TESTS=\"Basic Call - Mainline\""
   else
      docker exec -it live-test bash -c "source /etc/profile.d/rvm.sh && cd /opt/clearwater-live-test && rake test[default.svc.cluster.local] PROXY=$BONO_SIP_PROXY_IP ELLIS=$ELLIS_IP SIGNUP_CODE=\"secret\""
   fi
fi
