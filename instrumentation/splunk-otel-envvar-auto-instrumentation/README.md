# Linux Java Auto Instrumentation via Environment Variables

**Linux Java Auto Instrumentation via Environment Variables (`splunk-otel-envvar-auto-instrumentation`)** installs and
enables the [Splunk OpenTelemetry Auto Instrumentation Java Agent](
https://docs.splunk.com/Observability/gdi/get-data-in/application/java/splunk-java-otel-distribution.html) via the
`JAVA_TOOL_OPTIONS` environment variable to automatically instrument supported Java applications, send the captured
distributed traces to the locally running [Splunk OpenTelemetry Collector](
https://docs.splunk.com/Observability/gdi/opentelemetry/opentelemetry.html), and then on to [Splunk APM](
https://docs.splunk.com/Observability/apm/intro-to-apm.html).

## Prerequisites/Requirements

- Check [Java agent compatibility and requirements](
  https://docs.splunk.com/Observability/gdi/get-data-in/application/java/java-otel-requirements.html) for supported
  libraries/frameworks and Java versions.
- [Install](https://docs.splunk.com/Observability/gdi/opentelemetry/install-linux.html) the Splunk OpenTelemetry
  Collector.
- Debian or RPM based Linux distribution (amd64/x86_64 or arm64/aarch64).
- Supported Java application(s) running as `systemd` services or within Bourne-compatible login shells (`bash`, `ksh`,
  `zsh`, etc). ***Alternatively***, [install](
  https://docs.splunk.com/Observability/gdi/opentelemetry/auto-instrumentation/auto-instrumentation-java-linux.html)
  the `splunk-otel-auto-instrumentation` package to enable Auto Instrumentation with the
  [`libsplunk.so` shared object library](../splunk-otel-auto-instrumentation) for all Java processes, or
  [manually install and enable](
  https://docs.splunk.com/Observability/gdi/get-data-in/application/java/instrumentation/instrument-java-application.html#install-the-splunk-distribution-of-opentelemetry-java-manually)
  the Java agent for a particular application.

## Installation

The `splunk-otel-envvar-auto-instrumentation` deb/rpm package provides the following files to enable and configure the
Java agent for `systemd` services and Bourne-compatible login shells:
- [`/etc/profile.d/00-splunk-otel-javaagent.sh`](#login-shells): Drop-in file with the following default environment
  variables for Bourne-compatible login shells:
    - `JAVA_TOOL_OPTIONS=-javaagent:/usr/lib/splunk-instrumentation/splunk-otel-javaagent.jar`
    - `OTEL_JAVAAGENT_CONFIGURATION_FILE=/usr/lib/splunk-instrumentation/splunk-otel-javaagent.properties`
- [`/usr/lib/systemd/system.conf.d/00-splunk-otel-javaagent.conf`](#systemd): Drop-in file with the following default
  environment variables for `systemd` services:
    - `JAVA_TOOL_OPTIONS=-javaagent:/usr/lib/splunk-instrumentation/splunk-otel-javaagent.jar`
    - `OTEL_JAVAAGENT_CONFIGURATION_FILE=/usr/lib/splunk-instrumentation/splunk-otel-javaagent.properties`
- `/usr/lib/splunk-instrumentation/splunk-otel-javaagent.jar`: The [Splunk OpenTelemetry Auto Instrumentation Java
  Agent](https://docs.splunk.com/Observability/gdi/get-data-in/application/java/splunk-java-otel-distribution.html).
- [`/usr/lib/splunk-instrumentation/splunk-otel-javaagent.properties`](#configuration-file): The default system
  properties file to [configure the Splunk OpenTelemetry Auto Instrumentation Java Agent](
  https://docs.splunk.com/Observability/gdi/get-data-in/application/java/configuration/advanced-java-otel-configuration.html).

Install these packages from [package repositories](#debian-and-rpm-repositories) or download them from
[GitHub Releases](#debian-and-rpm-packages).

After installation, restart the applicable services or reboot the system to enable the Java agent with the default
configuration. Optionally, see [Configuration](#configuration) for details about configuring the agent.

### Debian and RPM Repositories

If the `splunk-otel-collector` deb/rpm package repository has not already been configured and enabled, set up the
package repository and install the `splunk-otel-envvar-auto-instrumentation` package (requires `root` privileges):
- Debian:
    ```shell
    curl -sSL https://splunk.jfrog.io/splunk/otel-collector-deb/splunk-B3CD4420.gpg > /etc/apt/trusted.gpg.d/splunk.gpg && \
    echo 'deb https://splunk.jfrog.io/splunk/otel-collector-deb release main' > /etc/apt/sources.list.d/splunk-otel-collector.list && \
    apt-get update && \
    apt-get install -y splunk-otel-envvar-auto-instrumentation
    ```
- RPM with `yum`:
    ```shell
    cat <<EOH > /etc/yum.repos.d/splunk-otel-collector.repo && yum install -y splunk-otel-envvar-auto-instrumentation
    [splunk-otel-collector]
    name=Splunk OpenTelemetry Collector Repository
    baseurl=https://splunk.jfrog.io/splunk/otel-collector-rpm/release/\$basearch
    gpgcheck=1
    gpgkey=https://splunk.jfrog.io/splunk/otel-collector-rpm/splunk-B3CD4420.pub
    enabled=1
    EOH
    ```
- RPM with `dnf`:
    ```shell
    cat <<EOH > /etc/yum.repos.d/splunk-otel-collector.repo && dnf install -y splunk-otel-envvar-auto-instrumentation
    [splunk-otel-collector]
    name=Splunk OpenTelemetry Collector Repository
    baseurl=https://splunk.jfrog.io/splunk/otel-collector-rpm/release/\$basearch
    gpgcheck=1
    gpgkey=https://splunk.jfrog.io/splunk/otel-collector-rpm/splunk-B3CD4420.pub
    enabled=1
    EOH
    ```
- RPM with `zypper`:
    ```shell
    cat <<EOH > /etc/zypp/repos.d/splunk-otel-collector.repo && zypper install -y splunk-otel-envvar-auto-instrumentation
    [splunk-otel-collector]
    name=Splunk OpenTelemetry Collector Repository
    baseurl=https://splunk.jfrog.io/splunk/otel-collector-rpm/release/\$basearch
    gpgcheck=1
    gpgkey=https://splunk.jfrog.io/splunk/otel-collector-rpm/splunk-B3CD4420.pub
    enabled=1
    EOH
    ```

### Debian and RPM Packages

Download and install the `splunk-otel-envvar-auto-instrumentation` package ***without*** setting up a
[package repository](#debian-and-rpm-repositories) (requires `root` privileges):
1. Download the appropriate `splunk-otel-envvar-auto-instrumentation` deb/rpm package for the target system
   (amd64/x86_64 or arm64/aarch64) from [GitHub Releases](https://github.com/signalfx/splunk-otel-collector/releases).
2. Download and install the public key for package signature verification:
   - Debian:
       ```shell
       curl -sSL https://splunk.jfrog.io/splunk/otel-collector-deb/splunk-B3CD4420.gpg > /etc/apt/trusted.gpg.d/splunk.gpg
       ```
   - RPM:
       ```shell
       rpm --import https://splunk.jfrog.io/splunk/otel-collector-rpm/splunk-B3CD4420.pub
       ```
3. Install the package with the following command (replace `<path>` with the local path to the downloaded package):
   - Debian:
       ```shell
       $ dpkg -i <path>
       ```
   - RPM:
       ```shell
       $ rpm -ivh <path>
       ```

## Configuration

See the [Advanced Configuration Guide](
https://docs.splunk.com/Observability/gdi/get-data-in/application/java/configuration/advanced-java-otel-configuration.html)
for details about supported options and defaults for the Java agent. These options can be configured via
[environment variables](#environment-variables) or their corresponding [system properties](#configuration-file)
after installation.

> ### Configuration Priority
> The Java agent can consume configuration from one or more of the following sources (ordered from highest to lowest
> priority):
> 1. Java system properties (`-D` flags) passed directly to the agent. For example,
>      ```shell
>      JAVA_TOOL_OPTIONS="-javaagent:/usr/lib/splunk-instrumentation/splunk-otel-javaagent.jar -Dotel.service.name=my-service"
>      ```
> 2. Environment variables
> 3. Configuration files
> 
> Before making any changes, check the configuration of the system or individual services for potential conflicts.

### Environment Variables

#### Login shells

The default [`/etc/profile.d/00-splunk-otel-javaagent.sh`](packaging/00-splunk-otel-javaagent.sh) drop-in file
defines the following environment variables for Bourne-compatible login shells to enable the Java agent and sets the
path to the default system properties file for agent configuration, respectively:
- `JAVA_TOOL_OPTIONS=-javaagent:/usr/lib/splunk-instrumentation/splunk-otel-javaagent.jar`
- `OTEL_JAVAAGENT_CONFIGURATION_FILE=/usr/lib/splunk-instrumentation/splunk-otel-javaagent.properties`

Any changes to this file will affect ***all*** login shells, unless overriden by [higher-priority](
#configuration-priority) system, application, or shell configurations.

To add/modify [supported environment variables](
https://docs.splunk.com/Observability/gdi/get-data-in/application/java/configuration/advanced-java-otel-configuration.html)
defined in `/etc/profile.d/00-splunk-otel-javaagent.sh` (requires `root` privileges):
1. **Option A**: Update `/etc/profile.d/00-splunk-otel-javaagent.sh` for the desired environment variables. For example:
     ```shell
     $ cat <<EOH > /etc/profile.d/00-splunk-otel-javaagent.sh
     export JAVA_TOOL_OPTIONS="-javaagent:/my/custom/splunk-otel-javaagent.jar -Dotel.service.name=my-service"
     export OTEL_JAVAAGENT_CONFIGURATION_FILE="/my/custom/splunk-otel-javaagent.properties"
     export SPLUNK_PROFILER_ENABLED="true"
     EOH
     ```
   **Option B**: Create/Modify a higher-priority drop-in file for ***all*** login shells to add or override the
   environment variables defined in `/etc/profile.d/00-splunk-otel-javaagent.sh`. For example:
     ```shell
     $ cat <<EOH >> /etc/profile.d/99-my-custom-env-vars.sh
     export JAVA_TOOL_OPTIONS="-javaagent:/my/custom/splunk-otel-javaagent.jar -Dotel.service.name=my-service"
     export OTEL_JAVAAGENT_CONFIGURATION_FILE="/my/custom/splunk-otel-javaagent.properties"
     export SPLUNK_PROFILER_ENABLED="true"
     EOH
     ```
   **Option C**: Create/Modify a higher-priority login profile for a ***specific*** user's Bourne-compatible shell to
   add or override the environment variables defined in `/etc/profile.d/00-splunk-otel-javaagent.sh`. For example:
     ```shell
     $ cat <<EOH >> $HOME/.profile
     export JAVA_TOOL_OPTIONS="-javaagent:/my/custom/splunk-otel-javaagent.jar -Dotel.service.name=my-service"
     export OTEL_JAVAAGENT_CONFIGURATION_FILE="/my/custom/splunk-otel-javaagent.properties"
     export SPLUNK_PROFILER_ENABLED="true"
     EOH
     ```
2. After any configuration changes, reboot the system or log out, log back in, and start the applicable
   services/applications for changes to take effect.

#### Systemd

The default [`/usr/lib/systemd/system.conf.d/00-splunk-otel-javaagent.conf`](
packaging/00-splunk-otel-javaagent.conf) `systemd` drop-in file defines the following environment variables to
enable the Java agent and sets the path to the default system properties file for agent configuration, respectively:
- `JAVA_TOOL_OPTIONS=-javaagent:/usr/lib/splunk-instrumentation/splunk-otel-javaagent.jar`
- `OTEL_JAVAAGENT_CONFIGURATION_FILE=/usr/lib/splunk-instrumentation/splunk-otel-javaagent.properties`

Any changes to this file will affect ***all*** `systemd` services, unless overriden by [higher-priority](
#configuration-priority) system or service configurations.

> ***Note***: `Systemd` supports many options/methods for configuring environment variables at the system level or for
> individual services, and are not limited to the examples below. Consult the documentation specific to your Linux
> distribution or service before making any changes. For general details about `systemd`, see the [`systemd` man page](
> https://www.freedesktop.org/software/systemd/man/index.html).

To add/modify [supported environment variables](
https://docs.splunk.com/Observability/gdi/get-data-in/application/java/configuration/advanced-java-otel-configuration.html)
defined in `/usr/lib/systemd/system.conf.d/00-splunk-otel-javaagent.conf` (requires `root` privileges):
1. **Option A**: Update `DefaultEnvironment` within `/usr/lib/systemd/system.conf.d/00-splunk-otel-javaagent.conf` for 
   the desired environment variables. For example:
     ```shell
     $ cat <<EOH > /usr/lib/systemd/system.conf.d/00-splunk-otel-javaagent.conf
     [Manager]
     DefaultEnvironment="JAVA_TOOL_OPTIONS=-javaagent:/my/custom/splunk-otel-javaagent.jar -Dotel.service.name=my-service"
     DefaultEnvironment="OTEL_JAVAAGENT_CONFIGURATION_FILE=/my/custom/splunk-otel-javaagent.properties"
     DefaultEnvironment="SPLUNK_PROFILER_ENABLED=true"
     EOH
     ```
   **Option B**: Create/Modify a higher-priority drop-in file for ***all*** services to add or override the environment
   variables defined in `/usr/lib/systemd/system.conf.d/00-splunk-otel-javaagent.conf`. For example:
     ```shell
     $ cat <<EOH > /usr/lib/systemd/system.conf.d/99-my-custom-env-vars.conf
     [Manager]
     DefaultEnvironment="JAVA_TOOL_OPTIONS=-javaagent:/my/custom/splunk-otel-javaagent.jar -Dotel.service.name=my-service"
     DefaultEnvironment="OTEL_JAVAAGENT_CONFIGURATION_FILE=/my/custom/splunk-otel-javaagent.properties"
     DefaultEnvironment="SPLUNK_PROFILER_ENABLED=true"
     EOH
     ```
   **Option C**: Create/Modify a higher-priority drop-in file for a ***specific*** service to add or override the
   environment variables defined in `/usr/lib/systemd/system.conf.d/00-splunk-otel-javaagent.conf`. For example:
     ```shell
     $ cat <<EOH > /usr/lib/systemd/system/my-service.d/99-my-custom-env-vars.conf
     [Service]
     Environment="JAVA_TOOL_OPTIONS=-javaagent:/my/custom/splunk-otel-javaagent.jar -Dotel.service.name=my-service"
     Environment="OTEL_JAVAAGENT_CONFIGURATION_FILE=/my/custom/splunk-otel-javaagent.properties"
     Environment="SPLUNK_PROFILER_ENABLED=true"
     EOH
     ```
2. After any configuration changes, reboot the system or run the following commands to restart the applicable services
   for the changes to take effect:
     ```shell
     $ systemctl daemon-reload
     $ systemctl restart <service-name>   # replace "<service-name>" and run for each applicable service
     ```

### Configuration file

The Java agent is configured by default (via the `OTEL_JAVAAGENT_CONFIGURATION_FILE` [environment variable](
#environment-variables)) to consume system properties from the
[`/usr/lib/splunk-instrumentation/splunk-otel-javaagent.properties`](packaging/splunk-otel-javaagent.properties)
configuration file.

Any changes to this file will affect ***all*** `systemd` services and applications running within login shells, unless
overriden by [higher-priority](#configuration-priority) system or service configurations.

To add/modify [supported system properties](
https://docs.splunk.com/Observability/gdi/get-data-in/application/java/configuration/advanced-java-otel-configuration.html)
in `/usr/lib/splunk-instrumentation/splunk-otel-javaagent.properties` (requires `root` privileges):
1. Update `/usr/lib/splunk-instrumentation/splunk-otel-javaagent.properties` for the desired system properties. For
   example:
     ```shell
     $ cat <<EOH > /usr/lib/splunk-instrumentation/splunk-otel-javaagent.properties
     # This is a comment
     otel.service.name=my-service
     otel.resource.attributes=deployment.environment=my-environment
     splunk.metrics.enabled=true
     splunk.profiler.enabled=true
     splunk.profiler.memory.enabled=true
     EOH
     ```
2. After any configuration changes, reboot the system or restart the applicable services/applications for the changes to
   take effect.

## Uninstall

1. If necessary, back up `/etc/profile.d/00-splunk-otel-javaagent.sh`,
   `/usr/lib/systemd/system.conf.d/00-splunk-otel-javaagent.conf`, and
   `/usr/lib/splunk-instrumentation/splunk-otel-javaagent.properties`.
2. Run the following command to uninstall the `splunk-otel-envvar-auto-instrumentation` package (requires `root`
   privileges):
   - Debian:
       ```shell
       dpkg -P splunk-otel-envvar-auto-instrumentation
       ```
   - RPM:
       ```shell
       rpm -e splunk-otel-envvar-auto-instrumentation
       ```
3. Reboot the system or restart the applicable services/applications for the changes to take effect.
