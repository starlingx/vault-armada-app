
{{/*
Generate certificates for vault CA
*/}}
{{- define "vault.gen-certs" -}}
{{- $altNames := list ( printf "%s.%s" (include "vault.name" .) .Release.Namespace ) ( printf "%s.%s.svc" (include "vault.name" .) .Release.Namespace ) -}}
{{- $ca := genCA "vault-ca" 365 -}}
{{- $cert := genSignedCert ( include "vault.name" . ) nil $altNames 365 $ca -}}
tls.crt: {{ $ca.Cert | b64enc }}
tls.key: {{ $ca.Key | b64enc }}
{{- end -}}