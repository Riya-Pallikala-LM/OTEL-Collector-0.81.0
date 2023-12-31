//go:build linux
// +build linux

package collectd

// AUTOGENERATED BY scripts/collectd-template-to-go.  DO NOT EDIT!!

import (
	"text/template"
)

// CollectdTemplate is a template for a collectd collectd config file
var CollectdTemplate = template.Must(InjectTemplateFuncs(template.New("collectd")).Parse(`
# Use a relative path because collectd will choke if the cwd is just '/' since
# it strips off trailing slashes from the path before doing the chdir.
BaseDir "{{ stripTrailingSlash .BundleDir }}/lib/.."
TypesDB "{{ stripTrailingSlash .BundleDir }}/types.db"
TypesDB "{{ stripTrailingSlash .BundleDir }}/signalfx_types.db"

PluginDir "{{ stripTrailingSlash .BundleDir }}/lib/collectd"

Hostname ""
FQDNLookup false
Interval {{ .IntervalSeconds }}
Timeout {{ .Timeout }}
ReadThreads {{ .ReadThreads }}
WriteThreads {{ .WriteThreads }}
WriteQueueLimitHigh {{ .WriteQueueLimitHigh }}
WriteQueueLimitLow  {{ .WriteQueueLimitLow }}
CollectInternalStats false

LoadPlugin logfile

<Plugin logfile>
  LogLevel "{{.LogLevel}}"
  Timestamp true
  PrintSeverity true
</Plugin>

LoadPlugin match_regex
LoadPlugin target_set

<Chain "PostCache">
  Target "write"
</Chain>

<LoadPlugin "write_http">
   FlushInterval 2
</LoadPlugin>
<Plugin "write_http">
  <Node "SignalFx">
    URL "{{.WriteServerURL}}{{.WriteServerQuery}}"
    Format "JSON"
    Timeout 5000
    BufferSize 4096
    LogHttpError true
  </Node>
</Plugin>

{{if .HasGenericJMXMonitor}}
LoadPlugin "java"

<Plugin java>
  #JVMArg "-verbose:jni"
  JVMArg "-Djava.class.path={{ stripTrailingSlash .BundleDir }}/collectd-java/collectd-api.jar:{{ stripTrailingSlash .BundleDir }}/collectd-java/generic-jmx.jar"

  LoadPlugin "org.collectd.java.GenericJMX"
</Plugin>
{{end}}

Include "{{.ManagedConfigDir}}/*.conf"
`)).Option("missingkey=error")
