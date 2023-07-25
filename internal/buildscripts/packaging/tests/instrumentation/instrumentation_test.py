# Copyright Splunk Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import glob
import os
import time

from pathlib import Path

import pytest
from iterators import TimeoutIterator

from tests.helpers.util import (
    copy_file_into_container,
    retry,
    run_container_cmd,
    run_distro_container,
    wait_for,
    wait_for_container_cmd,
    REPO_DIR,
    TESTS_DIR,
)


IMAGES_DIR = Path(__file__).parent.resolve() / "images"
DEB_DISTROS = [df.split(".")[-1] for df in glob.glob(str(IMAGES_DIR / "deb" / "Dockerfile.*"))]
RPM_DISTROS = [df.split(".")[-1] for df in glob.glob(str(IMAGES_DIR / "rpm" / "Dockerfile.*"))]

OTELCOL_BIN_DIR = REPO_DIR / "bin"
INSTALLER_PATH = REPO_DIR / "internal" / "buildscripts" / "packaging" / "installer" / "install.sh"
COLLECTOR_CONFIG_PATH = TESTS_DIR / "instrumentation" / "config.yaml"
JAVA_AGENT_PATH = "/usr/lib/splunk-instrumentation/splunk-otel-javaagent.jar"

PRELOAD_PKG_NAME = "splunk-otel-auto-instrumentation"
LIBSPLUNK_PATH = "/usr/lib/splunk-instrumentation/libsplunk.so"
DEFAULT_INSTRUMENTATION_CONF = "/usr/lib/splunk-instrumentation/instrumentation.conf"
CUSTOM_INSTRUMENTATION_CONF = TESTS_DIR / "instrumentation" / "instrumentation.conf"

ENVVAR_PKG_NAME = "splunk-otel-envvar-auto-instrumentation"
DEFAULT_SYSTEMD_CONF_PATH = "/usr/lib/systemd/system.conf.d/00-splunk-otel-javaagent.conf"
DEFAULT_PROFILE_PATH ="/etc/profile.d/00-splunk-otel-javaagent.sh"
DEFAULT_PROPERTIES_PATH = "/usr/lib/splunk-instrumentation/splunk-otel-javaagent.properties"
CUSTOM_PROPERTIES_PATH = TESTS_DIR / "instrumentation" / "splunk-otel-javaagent.properties"


def get_dockerfile(distro):
    if distro in DEB_DISTROS:
        return IMAGES_DIR / "deb" / f"Dockerfile.{distro}"
    else:
        return IMAGES_DIR / "rpm" / f"Dockerfile.{distro}"


def get_package(distro, name, arch):
    pkg_dir = REPO_DIR / "instrumentation" / name / "dist"
    pkg_paths = []
    if distro in DEB_DISTROS:
        pkg_paths = glob.glob(str(pkg_dir / f"{name}*{arch}.deb"))
    elif distro in RPM_DISTROS:
        if arch == "amd64":
            arch = "x86_64"
        elif arch == "arm64":
            arch = "aarch64"
        pkg_paths = glob.glob(str(pkg_dir / f"{name}*{arch}.rpm"))

    if pkg_paths:
        return sorted(pkg_paths)[-1]
    else:
        return None


def container_file_exists(container, path):
    return container.exec_run(f"test -f {path}").exit_code == 0


def install_package(container, distro, path):
    if distro in DEB_DISTROS:
        run_container_cmd(container, f"apt-get install -y {path}")
    elif "opensuse" in distro:
        run_container_cmd(container, f"zypper --no-gpg-checks install -y {path}")
    elif container.exec_run("command -v yum").exit_code == 0:
        run_container_cmd(container, f"yum install --setopt=obsoletes=0 -y {path}")
    elif container.exec_run("command -v dnf").exit_code == 0:
        run_container_cmd(container, f"dnf install --setopt=obsoletes=0 -y {path}")


def verify_installed_files(container, package):
    if package == PRELOAD_PKG_NAME:
        for path in [JAVA_AGENT_PATH, LIBSPLUNK_PATH, DEFAULT_INSTRUMENTATION_CONF]:
            assert container_file_exists(container, path), f"{path} not found"
        # verify /etc/ld.so.preload was updated for libsplunk.so
        run_container_cmd(container, f"grep '{LIBSPLUNK_PATH}' /etc/ld.so.preload")
    else:
        for path in [JAVA_AGENT_PATH, DEFAULT_PROPERTIES_PATH, DEFAULT_SYSTEMD_CONF_PATH, DEFAULT_PROFILE_PATH]:
            assert container_file_exists(container, path), f"{path} not found"
        # verify /etc/ld.so.preload was not updated for libsplunk.so
        if container_file_exists(container, "/etc/ld.so.preload"):
            assert container.exec_run(f"grep '{LIBSPLUNK_PATH}' /etc/ld.so.preload") != 0, \
                f"{LIBSPLUNK_PATH} found in /etc/ld.so.preload after {package} was installed"


def verify_tomcat_instrumentation(container, start_type, package, otelcol_path):
    if package == PRELOAD_PKG_NAME:
        # overwrite the default instrumentation.conf with the custom one for testing
        copy_file_into_container(container, CUSTOM_INSTRUMENTATION_CONF, DEFAULT_INSTRUMENTATION_CONF)
    else:
        # overwrite the default properties file with the custom one for testing
        copy_file_into_container(container, CUSTOM_PROPERTIES_PATH, DEFAULT_PROPERTIES_PATH)

    if start_type == "systemd":
        # restart the container and wait for systemd to be ready
        print("Restarting container ...")
        container.restart()
        wait_for_container_cmd(container, "systemctl show-environment", timeout=30)
        # start the collector and get the output stream
        stream = container.exec_run(f"{otelcol_path} --config=/test/config.yaml", stream=True).output
        time.sleep(5)
        print("Starting the tomcat systemd service ...")
        run_container_cmd(container, "systemctl start tomcat")
    else:
        # start the collector and get the output stream
        stream = container.exec_run(f"{otelcol_path} --config=/test/config.yaml", stream=True).output
        time.sleep(5)
        print("Starting tomcat from a login shell ...")
        tomcat_env = {
            "JAVA_HOME": "/opt/java/openjdk",
            "CATALINA_PID": "/usr/local/tomcat/temp/tomcat.pid",
            "CATALINA_HOME": "/usr/local/tomcat",
            "CATALINA_BASE": "/usr/local/tomcat",
            "CATALINA_OPTS": "-Xms512M -Xmx1024M -server -XX:+UseParallelGC",
            "JAVA_OPTS": "-Djava.awt.headless=true",
        }
        run_container_cmd(container, "bash -l -c /usr/local/tomcat/bin/startup.sh", env=tomcat_env)

    print("Waiting for http://127.0.0.1:8080/sample ...")
    wait_for_container_cmd(container, "curl -sSL http://127.0.0.1:8080/sample", timeout=180)

    # check the collector output stream for span/attributes
    start_time = time.time()
    config_source = "instrumentation_conf" if package == PRELOAD_PKG_NAME else "properties_file"
    target = "http.target: Str(/sample)"
    target_found = False
    service_name = f"service: Str(service_name_from_{config_source})"
    service_name_found = False
    deployment_environment = f"deployment_environment: Str(deployment_environment_from_{config_source})"
    deployment_environment_found = False
    profiling = "com.splunk.sourcetype: Str(otel.profiling)"
    profiling_found = False
    # currently, this metric is only generated by libsplunk.so (splunk-otel-auto-instrumentation)
    splunk_metric = "Name: splunk.linux-autoinstr.executions"
    splunk_metric_found = False
    for output in TimeoutIterator(stream, timeout=10, sentinel=None):
        if output:
            output = output.decode("utf-8").rstrip()
            print(output)
            if target in output:
                target_found = True
            if service_name in output:
                service_name_found = True
            if deployment_environment in output:
                deployment_environment_found = True
            if profiling in output:
                profiling_found = True
            if splunk_metric in output:
                splunk_metric_found = True
            if target_found and service_name_found and deployment_environment_found and profiling_found:
                if package == ENVVAR_PKG_NAME:
                    break
                elif package == PRELOAD_PKG_NAME and splunk_metric_found:
                    break
        if (time.time() - start_time) > 300:
            break

    assert target_found, f"timed out waiting for '{target}'"
    assert service_name_found, f"timed out waiting for '{service_name}'"
    assert deployment_environment_found, f"timed out waiting for '{deployment_environment}'"
    assert profiling_found, f"timed out waiting for '{profiling}'"
    if package == PRELOAD_PKG_NAME:
        assert splunk_metric_found, f"timed out waiting for '{splunk_metric}'"


@pytest.mark.parametrize(
    "distro",
    [pytest.param(distro, marks=pytest.mark.deb) for distro in DEB_DISTROS]
    + [pytest.param(distro, marks=pytest.mark.rpm) for distro in RPM_DISTROS],
    )
@pytest.mark.parametrize("package", [PRELOAD_PKG_NAME, ENVVAR_PKG_NAME])
@pytest.mark.parametrize("arch", ["amd64", "arm64"])
@pytest.mark.parametrize("start_type", ["systemd", "shell"])
def test_package_install(distro, package, arch, start_type):
    if distro == "opensuse-12" and arch == "arm64":
        pytest.skip("opensuse-12 arm64 no longer supported")

    otelcol_bin = f"otelcol_linux_{arch}"
    otelcol_bin_path = OTELCOL_BIN_DIR / otelcol_bin
    assert os.path.isfile(otelcol_bin_path), f"{otelcol_bin_path} not found!"

    pkg_path = get_package(distro, package, arch)
    assert pkg_path, f"{package} package not found"
    pkg_base = os.path.basename(pkg_path)

    with run_distro_container(distro, dockerfile=get_dockerfile(distro), arch=arch) as container:
        copy_file_into_container(container, COLLECTOR_CONFIG_PATH, "/test/config.yaml")
        copy_file_into_container(container, pkg_path, f"/test/{pkg_base}")
        copy_file_into_container(container, otelcol_bin_path, f"/test/{otelcol_bin}")
        run_container_cmd(container, f"chmod a+x /test/{otelcol_bin}")

        install_package(container, distro, f"/test/{pkg_base}")
        verify_installed_files(container, package)

        verify_tomcat_instrumentation(container, start_type, package, f"/test/{otelcol_bin}")


@pytest.mark.parametrize(
    "distro",
    [pytest.param(distro, marks=pytest.mark.deb) for distro in DEB_DISTROS]
    + [pytest.param(distro, marks=pytest.mark.rpm) for distro in RPM_DISTROS],
    )
@pytest.mark.parametrize("package", [PRELOAD_PKG_NAME, ENVVAR_PKG_NAME])
@pytest.mark.parametrize("arch", ["amd64", "arm64"])
@pytest.mark.parametrize("start_type", ["systemd", "shell"])
def test_package_replace(distro, package, arch, start_type):
    if distro == "opensuse-12" and arch == "arm64":
        pytest.skip("opensuse-12 arm64 no longer supported")

    otelcol_bin = f"otelcol_linux_{arch}"
    otelcol_bin_path = OTELCOL_BIN_DIR / otelcol_bin
    assert os.path.isfile(otelcol_bin_path), f"{otelcol_bin_path} not found!"

    old_pkg_path = get_package(distro, package, arch)
    assert old_pkg_path, f"{package} package not found"
    old_pkg_base = os.path.basename(old_pkg_path)

    new_package = ENVVAR_PKG_NAME if package == PRELOAD_PKG_NAME else PRELOAD_PKG_NAME
    new_pkg_path = get_package(distro, new_package, arch)
    assert new_pkg_path, f"{new_package} package not found"
    new_pkg_base = os.path.basename(new_pkg_path)

    with run_distro_container(distro, dockerfile=get_dockerfile(distro), arch=arch) as container:
        copy_file_into_container(container, COLLECTOR_CONFIG_PATH, "/test/config.yaml")
        copy_file_into_container(container, old_pkg_path, f"/test/{old_pkg_base}")
        copy_file_into_container(container, new_pkg_path, f"/test/{new_pkg_base}")
        copy_file_into_container(container, otelcol_bin_path, f"/test/{otelcol_bin}")
        run_container_cmd(container, f"chmod a+x /test/{otelcol_bin}")

        # add a comment to /etc/ld.so.preload
        run_container_cmd(container, "sh -c 'echo \"# This line should always be preserved\" >> /etc/ld.so.preload'")

        # install and verify the first package
        install_package(container, distro, f"/test/{old_pkg_base}")
        verify_installed_files(container, package)

        # verify the comment was preserved after first package install
        run_container_cmd(container, "grep '# This line should always be preserved' /etc/ld.so.preload")

        # install and verify the new package
        install_package(container, distro, f"/test/{new_pkg_base}")
        verify_installed_files(container, new_package)

        # verify the comment was preserved after new package install
        run_container_cmd(container, "grep '# This line should always be preserved' /etc/ld.so.preload")

        # verify libsplunk.so was uninstalled when splunk-otel-envvar-auto-instrumentation is installed
        if new_package == ENVVAR_PKG_NAME:
            assert not container_file_exists(container, LIBSPLUNK_PATH)

        # config files on debian/ubuntu will remain until the first package is purged
        if distro in DEB_DISTROS:
            run_container_cmd(container, f"apt purge -y {package}")

        # verify config files from the first package were uninstalled
        if new_package == PRELOAD_PKG_NAME:
            for path in [DEFAULT_PROFILE_PATH, DEFAULT_PROPERTIES_PATH, DEFAULT_SYSTEMD_CONF_PATH]:
                assert not container_file_exists(container, path)
        else:
            assert not container_file_exists(container, DEFAULT_INSTRUMENTATION_CONF)

        verify_tomcat_instrumentation(container, start_type, new_package, f"/test/{otelcol_bin}")


@pytest.mark.parametrize(
    "distro",
    [pytest.param(distro, marks=pytest.mark.deb) for distro in DEB_DISTROS]
    + [pytest.param(distro, marks=pytest.mark.rpm) for distro in RPM_DISTROS],
    )
@pytest.mark.parametrize("package", [PRELOAD_PKG_NAME, ENVVAR_PKG_NAME])
@pytest.mark.parametrize("arch", ["amd64", "arm64"])
def test_package_uninstall(distro, package, arch):
    if distro == "opensuse-12" and arch == "arm64":
        pytest.skip("opensuse-12 arm64 no longer supported")

    pkg_path = get_package(distro, package, arch)
    assert pkg_path, f"{package} package not found"
    pkg_base = os.path.basename(pkg_path)

    with run_distro_container(distro, dockerfile=get_dockerfile(distro), arch=arch) as container:
        copy_file_into_container(container, pkg_path, f"/test/{pkg_base}")

        # install the package
        install_package(container, distro, f"/test/{pkg_base}")

        verify_installed_files(container, package)

        # uninstall the package
        if distro in DEB_DISTROS:
            run_container_cmd(container, f"apt-get purge -y {package}")
        elif "opensuse" in distro:
            run_container_cmd(container, f"zypper remove -y {package}")
        elif container.exec_run("command -v yum").exit_code == 0:
            run_container_cmd(container, f"yum remove -y {package}")
        elif container.exec_run("command -v dnf").exit_code == 0:
            run_container_cmd(container, f"dnf remove -y {package}")

        # verify the package was uninstalled
        if distro in DEB_DISTROS:
            assert container.exec_run(f"dpkg -s {package}").exit_code != 0
        else:
            assert container.exec_run(f"rpm -q {package}").exit_code != 0

        # verify files were uninstalled
        if package == PRELOAD_PKG_NAME:
            for path in [DEFAULT_PROFILE_PATH, DEFAULT_PROPERTIES_PATH, DEFAULT_SYSTEMD_CONF_PATH]:
                assert not container_file_exists(container, path)
        else:
            for path in [LIBSPLUNK_PATH, DEFAULT_INSTRUMENTATION_CONF]:
                assert not container_file_exists(container, path)
