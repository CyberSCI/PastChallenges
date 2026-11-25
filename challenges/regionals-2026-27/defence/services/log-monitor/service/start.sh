#!/usr/bin/env bash
#
# CyberSci Regionals 2026/27
#
# Log Monitor by Dmitriy Beryoza (0xd13a@gmail.com)

set -euo pipefail
es_pid= kb_pid= ls_pid=
stop() {
  trap - EXIT TERM INT
  for pid in "$es_pid" "$kb_pid" "$ls_pid"; do
    if [[ -n "$pid" ]]; then kill "$pid" 2>/dev/null || true; fi
  done
  wait 2>/dev/null || true
}
trap stop EXIT TERM INT

/opt/elk/elasticsearch/bin/elasticsearch & es_pid=$!
for ((attempt=0; attempt<120; attempt++)); do
  if curl -fsS http://127.0.0.1:9200/_cluster/health >/dev/null 2>&1; then break; fi
  kill -0 "$es_pid" 2>/dev/null || { echo 'Elasticsearch exited' >&2; exit 1; }
  if ((attempt == 119)); then echo 'Elasticsearch startup timed out' >&2; exit 1; fi
  sleep 2
done

/opt/elk/kibana/bin/kibana & kb_pid=$!

/opt/elk/logstash/bin/logstash --path.settings /opt/elk/logstash/config -f /opt/elk/logstash/pipeline.conf & ls_pid=$!

for ((attempt=0; attempt<120; attempt++)); do
    if curl -fsS http://127.0.0.1:5601/api/status >/dev/null 2>&1; then break; fi
    kill -0 "$kb_pid" 2>/dev/null || { echo 'Kibana exited before Canvas import' >&2; exit 1; }
    kill -0 "$ls_pid" 2>/dev/null || { echo 'Logstash exited before Canvas import' >&2; exit 1; }
    if ((attempt == 119)); then echo 'Kibana startup timed out' >&2; exit 1; fi
    sleep 2
done

curl --show-error \
  -X POST 'http://127.0.0.1:5601/api/canvas/workpad' \
  -H 'kbn-xsrf: true' \
  -H 'Content-Type: application/json' \
  --data-binary @/tmp/canvas-workpad.json

wait -n "$es_pid" "$kb_pid" "$ls_pid" || true
echo 'An ELK process exited; stopping the stack.' >&2
exit 1
