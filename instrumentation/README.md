# Splunk OpenTelemetry Zero Configuration Auto Instrumentation for Java

**Splunk OpenTelemetry Zero Configuration Auto Instrumentation for Java** installs and enables the
[Splunk OpenTelemetry Auto Instrumentation Java Agent](
https://docs.splunk.com/Observability/gdi/get-data-in/application/java/splunk-java-otel-distribution.html) to
automatically instrument supported Java applications on Linux, send the captured distributed traces to the locally
running [Splunk OpenTelemetry Collector](
https://docs.splunk.com/Observability/gdi/opentelemetry/opentelemetry.html), and then on to [Splunk APM](
https://docs.splunk.com/Observability/apm/intro-to-apm.html).

## Debian/RPM Package Options

- **[`splunk-otel-auto-instrumentation`](./splunk-otel-auto-instrumentation)**: Installs the Java agent, the
  `libsplunk.so` shared object library, and adds `libsplunk.so` to `/etc/ld.so.preload` to automatically monitor and set
  the `JAVA_TOOL_OPTIONS:-javaagent:/usr/lib/splunk-instrumentation/splunk-otel-javaagent.jar` and other environment
  variables for ***all*** Java processes on the system.

- **[`splunk-otel-envvar-auto-instrumentation`](./splunk-otel-envvar-auto-instrumentation)**: Installs the Java agent
  and enables Auto Instrumentation by setting the
  `JAVA_TOOL_OPTIONS:-javaagent:/usr/lib/splunk-instrumentation/splunk-otel-javaagent.jar` and other environment
  variables for Java applications running as `systemd` services and within Bourne-compatible login shells via drop-in
  files.

> ### Notes
> 1. The [`splunk.linux-autoinstr.executions`](./splunk-otel-auto-instrumentation#disable_telemetry-optional) metric is
>    only available with the `splunk-otel-auto-instrumentation` package.
> 2. The configuration files and the options defined within are only applicable for the respective package that is
>    installed. For example, `/usr/lib/splunk-instrumentation/instrumentation.conf` is only applicable with
>    `splunk-otel-auto-instrumentation`, and `/usr/lib/splunk-instrumentation/splunk-otel-javaagent.properties` is only
>    applicable with `splunk-otel-envvar-auto-instrumentation`. Furthermore, migration from one package to another does
>    ***not*** automatically migrate the options from the old configuration file to the new one.
