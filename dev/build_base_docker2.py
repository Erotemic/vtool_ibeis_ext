import ubelt as ub
import os

BS = chr(92)  # backslash
NL = chr(10)  # newline
CMD_SEP = f' && {BS}{NL}'


def argval(clikey, envkey=None, default=ub.NoParam):
    if envkey is not None:
        envval = os.environ.get(envkey)
        if envval:
            default = envval
    return ub.argval(clikey, default=default)


def make_fletch_parts(fletch_version, dpath, remain):
    fletch_init_commands = []
    fletch_version = 'v1.5.0'
    dpath = ub.Path(ub.get_app_cache_dir('erotemic/manylinux-for/workspace2'))

    fletch_parts = []

    USE_STAGING_STRATEGY = False
    if USE_STAGING_STRATEGY:
        staging_dpath = (dpath / 'staging').ensuredir()
        fletch_dpath = staging_dpath / 'fletch'
        if not fletch_dpath.exists():
            # TODO: setup a dummy build on the host machine that
            # pre-downloads all the requirements so we can stage them
            ub.cmd('git clone -b @v1.5.0 https://github.com/Kitware/fletch.git', cwd=staging_dpath)
        ub.cmd(f'git checkout {fletch_version}', cwd=fletch_dpath)
        fletch_parts.append(ub.codeblock(
            '''
            COPY ./staging/fletch /root/code/fletch
            '''))
        fletch_init_commands.extend([
            'mkdir -p /root/code/fletch/build',
            'cd /root/code/fletch/build',
        ])
    else:
        # Clone specific branch with no tag history
        fletch_init_commands.extend([
            'cd /root/code',
            'git clone -b v1.5.0 --depth 1 https://github.com/Kitware/fletch.git fletch',
            'mkdir -p /root/code/fletch/build',
            'cd /root/code/fletch/build',
        ])

    cmake_flags = []
    if 'opencv' in remain:
        cmake_flags += [
            '-Dfletch_ENABLE_OpenCV=True',
            '-DOpenCV_SELECT_VERSION=4.2.0',
        ]
        remain.remove('opencv')

    if 'zlib' in remain:
        cmake_flags += [
            '-Dfletch_ENABLE_ZLib=True',
        ]
        remain.remove('zlib')

    cmake_flags += [
        '-DCMAKE_BUILD_TYPE=Release'
    ]

    cmake_flag_text = ' '.join(cmake_flags)

    fletch_init_commands.append(ub.codeblock(
        fr'''
        cmake {cmake_flag_text} ..
        '''))
    fletch_init_commands.extend([
        'make -j$(getconf _NPROCESSORS_ONLN)',
        'make install',
        'rm -rf /root/code/fletch',
    ])
    fletch_init_run_command = ub.indent(CMD_SEP.join(fletch_init_commands)).lstrip()
    fletch_parts.append(f'RUN {fletch_init_run_command}')
    return fletch_parts


class PackageManager:
    def __init__(self, distribution):
        self.distribution = distribution
        self.dist_to_manager = {
            'centos': 'yum',
            'debian': 'apt',
            'alpine': 'apk',
        }
        package_manager_maps = {}
        package_manager_maps['yum'] = {
            'lz4': ['lz4-devel'],
            # 'zlib': ['zlib-devel'],  # The yum version of zlib is too old
            'build': ['gcc', 'gcc-c++', 'make'],
            'fortran': ['gcc-gfortran'],
        }
        package_manager_maps['debian'] = {
            'zlib': 'zlib1g-dev',  # Not sure if this is too old or not
            'lz4': 'liblz4-dev',
        }
        package_manager_maps['alpine'] = {
            'zlib': 'zlib-dev',  # Not sure if this is too old or not
            'lz4': 'lz4-dev',
        }
        self.package_manager_maps = package_manager_maps

    def find_installable(self, included_packages):
        manager = self.dist_to_manager[self.distribution]
        known = self.package_manager_maps[manager]
        remain = ub.oset(included_packages) - ub.oset(known)
        installable = ub.oset(included_packages) - remain
        return installable, remain

    def make_install_parts(self, installable):
        manager = self.dist_to_manager[self.distribution]
        manager_packages = ub.udict(self.package_manager_maps[manager])
        libs = list(ub.flatten(manager_packages.take(installable)))
        parts = []
        if len(libs):
            if manager == 'yum':
                yum_libs_str = ' '.join(libs)
                yum_parts = [
                    'yum update -y',
                    f'yum install {yum_libs_str} -y',
                    'yum clean all',
                ]
                yum_install_cmd = ub.indent(CMD_SEP.join(yum_parts)).lstrip()
                parts.append(f'RUN {yum_install_cmd}')
            elif manager == 'apt':
                apt_libs_str = ' '.join(libs)
                apt_parts = [
                    'apt-get update',
                    'apt-get install',
                    f'apt-get install {apt_libs_str} -y',
                    'rm -rf /var/lib/apt/lists/*',
                ]
                apt_install_cmd = ub.indent(CMD_SEP.join(apt_parts)).lstrip()
                parts.append(f'RUN {apt_install_cmd}')
            elif manager == 'apk':
                apt_libs_str = ' '.join(libs)
                apt_parts = [
                    f'apk add --update-cache {apt_libs_str}',
                    'rm -rf /var/cache/apk/*',
                ]
                apk_install_cmd = ub.indent(CMD_SEP.join(apt_parts)).lstrip()
                parts.append(f'RUN {apk_install_cmd}')
        return parts


def main():
    fletch_version = 'v1.5.0'
    ARCH = argval('--arch', 'ARCH', default='x86_64')
    PARENT_IMAGE_PREFIX = argval('--parent_image_prefix', 'PARENT_IMAGE_PREFIX', default='manylinux2014')
    # PARENT_IMAGE_PREFIX = 'manylinux_2_24'
    # PARENT_IMAGE_PREFIX = 'manylinux2014'

    PARENT_IMAGE_BASE = f'{PARENT_IMAGE_PREFIX}_{ARCH}'
    PARENT_IMAGE_TAG = 'latest'
    PARENT_IMAGE_NAME = f'{PARENT_IMAGE_BASE}:{PARENT_IMAGE_TAG}'

    PARENT_QUAY_USER = 'quay.io/pypa'
    PARENT_IMAGE_URI = f'{PARENT_QUAY_USER}/{PARENT_IMAGE_NAME}'

    OUR_QUAY_USER = 'quay.io/erotemic'
    OUR_IMAGE_BASE = f'{PARENT_IMAGE_BASE}_for'

    included_packages = []

    if ub.argflag('--lz4'):
        included_packages.append('lz4')

    if ub.argflag('--opencv'):
        included_packages.append('opencv')

    if ub.argflag('--zlib'):
        included_packages.append('zlib')

    if ub.argflag('--build'):
        included_packages.append('build')

    if ub.argflag('--fortran'):
        included_packages.append('fortran')

    if ub.argflag('--gsl'):
        included_packages.append('gsl')

    # included_packages = [
    #     'lz4',
    #     # 'opencv',
    # ]
    pkg_suffix = '-'.join(included_packages)

    OUR_IMAGE_TAG = pkg_suffix
    OUR_IMAGE_NAME = f'{OUR_IMAGE_BASE}:{OUR_IMAGE_TAG}'

    OUR_DOCKER_URI = f'{OUR_QUAY_USER}/{OUR_IMAGE_NAME}'
    DRY = ub.argflag('--dry')

    dpath = ub.Path(ub.get_app_cache_dir('erotemic/manylinux-for/workspace2'))

    dockerfile_fpath = dpath / f'{OUR_IMAGE_BASE}.{OUR_IMAGE_TAG}.Dockerfile'

    if PARENT_IMAGE_PREFIX == 'manylinux2014':
        distribution = 'centos'
    elif PARENT_IMAGE_PREFIX == 'manylinux_2_24':
        distribution = 'debian'
    elif PARENT_IMAGE_PREFIX == 'musllinux_1_1':
        distribution = 'alpine'
    else:
        raise KeyError(PARENT_IMAGE_PREFIX)

    parts = []
    parts.append(ub.codeblock(
        f'''
        FROM {PARENT_IMAGE_URI}
        SHELL ["/bin/bash", "-c"]
        ENV HOME=/root
        RUN mkdir -p /root/code
        '''))
    # ENV ARCH={ARCH}

    pman = PackageManager(distribution)
    installable, remain = pman.find_installable(included_packages)

    parts += pman.make_install_parts(installable)

    if remain:
        # Use fletch to get the remaining libs
        parts += make_fletch_parts(fletch_version, dpath, remain)

    if 'gsl' in remain:
        parts.append('RUN ' + CMD_SEP.join([
            '  curl https://ftp.gnu.org/gnu/gsl/gsl-2.7.1.tar.gz  > gsl.tar.gz',
            '  tar xfv gsl.tar.gz',
            '  cd gsl-2.7.1',
            '  ./configure --prefix=/usr --disable-static',
            '  make && make install',
            '  cd .. && rm -rf gsl.tar.gz gsl-2.7.1'
        ]))

    docker_code = '\n\n'.join(parts)

    try:
        print(ub.color_text('\n--- DOCKER CODE ---', 'white'))
        print(ub.highlight_code(docker_code, 'docker'))
        print(ub.color_text('--- END DOCKER CODE ---\n', 'white'))
    except Exception:
        pass

    dockerfile_fpath.parent.ensuredir()
    with open(dockerfile_fpath, 'w') as file:
        file.write(docker_code)

    docker_build_cli = ' '.join([
        'docker', 'build',
        '--tag {}'.format(OUR_IMAGE_NAME),
        '-f {}'.format(dockerfile_fpath),
        '.'
    ])
    print('docker_build_cli = {!r}'.format(docker_build_cli))

    if DRY:
        print('DRY RUN: Would run')
        print(f'docker pull {PARENT_IMAGE_URI}')
        print(f'cd {dpath}')
        print(docker_build_cli)
    else:
        ub.cmd(f'docker pull {PARENT_IMAGE_URI}', verbose=3)
        info = ub.cmd(docker_build_cli, cwd=dpath, verbose=3, shell=True, check=True)

        if info['ret'] != 0:
            print(ub.color_text('\n--- FAILURE ---', 'red'))
            print('Failed command:')
            print(info['command'])
            print(info['err'])
            raise Exception('Building docker failed with exit code {}'.format(info['ret']))
        else:
            print(ub.color_text('\n--- SUCCESS ---', 'green'))

        print(ub.highlight_code(ub.codeblock(
            f'''
            # Finished creating the docker image.
            # To test / export / publish you can do something like this:

            # Test that we can get a bash terminal
            docker run -it {OUR_IMAGE_NAME} bash

            docker save -o {OUR_IMAGE_NAME}.docker.tar {OUR_IMAGE_NAME}

            # To publish to quay

            source $(secret_loader.sh)
            echo "QUAY_USERNAME = $QUAY_USERNAME"
            docker login -u $QUAY_USERNAME -p $QUAY_PASSWORD quay.io

            docker tag {OUR_IMAGE_NAME} {OUR_DOCKER_URI}
            docker push {OUR_DOCKER_URI}
            '''), 'bash'))


if __name__ == '__main__':
    """
    CommandLine:
        python ~/code/vtool_ibeis_ext/dev/build_base_docker2.py --dry

        python ~/code/vtool_ibeis_ext/dev/build_base_docker2.py --arch=x86_64 --parent_image_prefix=manylinux2014 --build --zlib --fortran --gsl
        python ~/code/vtool_ibeis_ext/dev/build_base_docker2.py --arch=i686 --parent_image_prefix=manylinux2014 --build --zlib --fortran --gsl

        python ~/code/vtool_ibeis_ext/dev/build_base_docker2.py --arch=x86_64 --parent_image_prefix=manylinux2014 --opencv
        python ~/code/vtool_ibeis_ext/dev/build_base_docker2.py --arch=i686 --parent_image_prefix=manylinux2014 --opencv

        python ~/code/vtool_ibeis_ext/dev/build_base_docker2.py --arch=x86_64 --parent_image_prefix=manylinux2014 --lz4
        python ~/code/vtool_ibeis_ext/dev/build_base_docker2.py --arch=i686 --parent_image_prefix=manylinux2014 --lz4



        OLD IMAGES

        python ~/code/vtool_ibeis_ext/dev/build_base_docker2.py --arch=x86_64 --parent_image_prefix=manylinux_2_24 --opencv
        python ~/code/vtool_ibeis_ext/dev/build_base_docker2.py --arch=i686 --parent_image_prefix=manylinux_2_24 --opencv

        python ~/code/vtool_ibeis_ext/dev/build_base_docker2.py --arch=x86_64 --parent_image_prefix=musllinux_1_1 --opencv
        python ~/code/vtool_ibeis_ext/dev/build_base_docker2.py --arch=i686 --parent_image_prefix=musllinux_1_1 --opencv

        python ~/code/vtool_ibeis_ext/dev/build_base_docker2.py --arch=x86_64 --parent_image_prefix=manylinux_2_24 --lz4
        python ~/code/vtool_ibeis_ext/dev/build_base_docker2.py --arch=i686 --parent_image_prefix=manylinux_2_24 --lz4

        python ~/code/vtool_ibeis_ext/dev/build_base_docker2.py --arch=x86_64 --parent_image_prefix=musllinux_1_1 --lz4
        python ~/code/vtool_ibeis_ext/dev/build_base_docker2.py --arch=i686 --parent_image_prefix=musllinux_1_1 --lz4

        python ~/code/vtool_ibeis_ext/dev/build_base_docker2.py --arch=x86_64 --parent_image_prefix=musllinux_1_1 --lz4
        python ~/code/vtool_ibeis_ext/dev/build_base_docker2.py --arch=i686 --parent_image_prefix=musllinux_1_1 --lz4

        python ~/code/vtool_ibeis_ext/dev/build_base_docker2.py --arch=aarch64 --dry

        # Then to build with CIBW
        pip install cibuildwheel
        CIBW_BUILD='cp*-manylinux_x86_64' CIBW_MANYLINUX_X86_64_IMAGE=quay.io/erotemic/manylinux-for:x86_64-fletch1.5.0-opencv cibuildwheel --platform linux --archs x86_64


    """
    main()
