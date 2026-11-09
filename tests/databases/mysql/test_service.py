import os
import pathlib
import subprocess

import pytest

from testsuite.databases.mysql import classes, service


def test_launcher_isolates_storage_and_preserves_environment(tmp_path):
    env = {'WORKER_SUFFIX': 'worker', 'EXTRA_ENV': 'preserved'}
    servers = [
        service.create_service(
            'mysql',
            tmp_path,
            classes.ServiceSettings(port=port),
            env,
        )
        for port in [12345, 23456]
    ]
    for server, port in zip(servers, [12345, 23456]):
        assert server._environment == {
            **env,
            'MYSQL_PORT': str(port),
            'MYSQL_TMPDIR': str(tmp_path / f'mysql-{port}'),
        }
    first, second = servers
    first._started_mark.create()
    assert not second._started_mark.exists()
    second._started_mark.create()
    first._started_mark.delete()
    assert second._started_mark.exists()
    assert env == {'WORKER_SUFFIX': 'worker', 'EXTRA_ENV': 'preserved'}


def test_launcher_default_settings(monkeypatch, tmp_path):
    monkeypatch.setenv('TESTSUITE_MYSQL_PORT', '23456')
    server = service.create_service('mysql', tmp_path)
    assert server._environment['MYSQL_PORT'] == '23456'
    assert server._environment['MYSQL_TMPDIR'] == str(tmp_path / 'mysql-23456')


@pytest.mark.parametrize('ramdisk_available', [False, True])
def test_script_isolates_data_by_port(tmp_path, ramdisk_available):
    script = service.SCRIPTS_DIR / 'service-mysql'
    utils_script = (
        pathlib.Path(service.service.__file__).parent / 'scripts/utils.sh'
    )
    utils_wrapper = tmp_path / 'utils.sh'
    utils_wrapper.write_text(f'''
        . "{utils_script}"
        mkdir() {{ return {0 if ramdisk_available else 1}; }}
        script_main() {{ printf '%s\\n' "$MYSQL_BASEDIR"; }}
    ''')
    for binary in ['mysqld', 'mysqladmin']:
        executable = tmp_path / binary
        executable.write_text('#!/bin/sh\necho "MySQL test binary"\n')
        executable.chmod(0o755)

    paths = []
    for port in [12345, 23456]:
        working_dir = tmp_path / f'mysql-{port}'
        result = subprocess.run(
            ['sh', str(script)],
            env={
                **os.environ,
                'PATH': f'{tmp_path}:{os.environ["PATH"]}',
                'TESTSUITE_LIB_UTILS': str(utils_wrapper),
                'WORKER_SUFFIX': 'worker',
                'USER': 'test-user',
                'MYSQL_PORT': str(port),
                'MYSQL_TMPDIR': str(working_dir),
            },
            capture_output=True,
            text=True,
            check=True,
        )
        path = result.stdout.strip()
        if ramdisk_available:
            assert path == f'/mnt/ramdisk/test-user/_mysql/worker/mysql-{port}'
        else:
            assert path == str(working_dir)
        paths.append(path)
    assert paths[0] != paths[1]
