#!/bin/sh
cd /run/reload && until grep -q 'nginx: master' /proc/1/cmdline; do sleep 1; done &&
while touch status && sleep 1; do
    if [ "$(cat status)" = reload ]; then
        if nginx -t -q && nginx -s reload; then printf ok; else printf failed; fi > status.new
        mv status.new status
    fi
done &
