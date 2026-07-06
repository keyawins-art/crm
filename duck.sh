#!/bin/bash
echo url="https://www.duckdns.org/update?domains=keyacrm&token=79223890-553e-4205-bb35-b7f659ca00ad&ip=192.168.1.16" | curl -k -o ~/duckdns/duck.log -K -
