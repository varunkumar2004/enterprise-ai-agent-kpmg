{{- define "assistant-api.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "assistant-api.fullname" -}}
{{- printf "%s-%s" .Release.Name (include "assistant-api.name" .) | trunc 63 | trimSuffix "-" }}
{{- end }}
