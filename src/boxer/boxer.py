#!/usr/bin/env python

"""BOXER
=====

This tool automates and facilitate testing of your dockerized multi-component application.

Involving "docker-compose", the "boxer" script helps you to create an isolated docker network
that simulates real-time execution of your dockerized application.

The "boxer" tool generates a docker-compose YAML file for you based on your pre-configurations
and then with a single command you spawn a running real-time environment where each component
is already initialized and they are all interconnected nicely with each other and isolated.

Additional component is usually added to the docker-compose network to be able to orchestrate
behavior of your application and later verify the outcome and thus test your multi-component application.
The orchestrator container can use for example "pytest" or "robotframework" to define a set
of tests that you may want to automate as part of your CI/CD.

Using the boxer tool involves the following steps:
    init    Generates initial setup with all files and sub-folders for your new simulation
    build   This will build all of the containers and cache locally the docker images
    start   Will spawn all of the containers in the target network group from cached docker images
    exec    Executes a command via shell inside of one of the running containers
    stop    Terminates all running containers in the target network group

"""

import os
import sys
import argparse
import subprocess


VERBOSE = ''
QUITE_PULL = ''
ALIAS = ''


def check_ret(ret):
    if ret == 0:
        return
    print('<BOXER> FAILED!')
    sys.exit(ret)


def no_comments(src):
    out = ''
    for line in src.splitlines(keepends=True):
        if line.strip().startswith('#'):
            continue
        out += line
    return out


def generate_docker_compose_build_file(group_name):
    yml = ''
    if os.path.isfile(os.path.join(group_name, 'build.header.yml')):
        yml += no_comments(open(os.path.join(group_name, 'build.header.yml')).read())
    else:
        yml += """version: '3.1'

services:

"""
    for box_name in os.listdir(group_name):
        if not box_name.startswith('box.'):
            continue
        if not os.path.isdir(os.path.join(group_name, box_name)):
            continue
        if not os.path.isfile(os.path.join(group_name, box_name, 'build.yml')):
            continue
        yml += no_comments(open(os.path.join(group_name, box_name, 'build.yml')).read()) + '\n'
    if os.path.isfile(os.path.join(group_name, 'build.footer.yml')):
        yml += no_comments(open(os.path.join(group_name, 'build.footer.yml')).read())
    open(os.path.join(group_name, 'docker-compose.build.yml'), 'w').write(yml)
    print(f'<BOXER> generated [{group_name}/docker-compose.build.yml] file')


def generate_docker_compose_run_file(group_name):
    yml = ''
    if os.path.isfile(os.path.join(group_name, 'run.header.yml')):
        yml += no_comments(open(os.path.join(group_name, 'run.header.yml')).read())
    else:
        yml += """version: '3.1'

services:

"""
    for box_name in os.listdir(group_name):
        if not box_name.startswith('box.'):
            continue
        if not os.path.isdir(os.path.join(group_name, box_name)):
            continue
        if not os.path.isfile(os.path.join(group_name, box_name, 'run.yml')):
            continue
        yml += no_comments(open(os.path.join(group_name, box_name, 'run.yml')).read()) + '\n'
    if os.path.isfile(os.path.join(group_name, 'run.footer.yml')):
        yml += no_comments(open(os.path.join(group_name, 'run.footer.yml')).read())
    open(os.path.join(group_name, 'docker-compose.run.yml'), 'w').write(yml)
    print(f'<BOXER> generated [{group_name}/docker-compose.run.yml] file')


def execute_docker_compose_build_down(group_name):
    print(f'<BOXER> executing [docker-compose -p build{ALIAS} down] in {group_name}/')
    return os.system(f"/bin/bash -c 'cd {group_name} && docker-compose -p build{ALIAS} down --volumes' {VERBOSE}")


def execute_docker_compose_run_down(group_name):
    print(f'<BOXER> executing [docker-compose -p {ALIAS} down] in {group_name}/')
    return os.system(f"/bin/bash -c 'docker-compose -p {ALIAS} down --volumes' {VERBOSE}")


def execute_docker_compose_build(group_name):
    print(f'<BOXER> executing [docker-compose -p build{ALIAS} up] in {group_name}/')
    return os.system(f"/bin/bash -c 'cd {group_name} && docker-compose -p build{ALIAS} -f docker-compose.build.yml up --detach --build {QUITE_PULL}' {VERBOSE}")


def execute_docker_compose_run(group_name):
    print(f'<BOXER> executing [docker-compose -p {ALIAS} up] in {group_name}/')
    return os.system(f"/bin/bash -c 'cd {group_name} && docker-compose -p {ALIAS} -f docker-compose.run.yml up --build {QUITE_PULL}' {VERBOSE}")


def execute_docker_compose_run_exec(group_name, container, command):
    print(f'<BOXER> executing [docker-compose -p {ALIAS} exec -T {container}] in {group_name}/')
    cmd = ['docker-compose', '-p', f'{ALIAS}', 'exec', '-T', f'{container}', ]
    cmd.extend(command)
    try:
        return subprocess.check_call(cmd)
    except subprocess.CalledProcessError as e:
        return e.returncode


def execute_docker_exec(group_name):
    exec_order = []
    for box_name in os.listdir(group_name):
        if not box_name.startswith('box.'):
            continue
        if not os.path.isdir(os.path.join(group_name, box_name)):
            continue
        if os.path.isfile(os.path.join(group_name, box_name, 'exec.sh')):
            exec_order.append((0, box_name, ))
            continue
        for filename in os.listdir(os.path.join(group_name, box_name)):
            if filename.startswith('exec-') and filename.endswith('.sh'):
                exec_order.append((int(filename.replace('exec-', '').replace('.sh', '')), box_name, ))
                break
    exec_order.sort(key=lambda item: item[0])
    for order_position, box_name in exec_order:
        filename = 'exec.sh' if order_position == 0 else 'exec-{}.sh'.format(order_position)
        print(f'<BOXER> executing [{filename}] in {group_name}/{box_name}/')
        cd_path = os.path.join(group_name, box_name)
        ret = os.system(f"/bin/bash -c 'cd {cd_path} && /bin/bash {filename}' {VERBOSE}")
        if ret != 0:
            return ret
    return 0


def execute_checkout(group_name):
    for box_name in os.listdir(group_name):
        if not box_name.startswith('box.'):
            continue
        if not os.path.isdir(os.path.join(group_name, box_name)):
            continue
        if not os.path.isfile(os.path.join(group_name, box_name, 'checkout.sh')):
            continue
        print(f'<BOXER> executing [checkout.sh] in {group_name}/{box_name}/')
        cd_path = os.path.join(group_name, box_name)
        ret = os.system(f"/bin/bash -c 'cd {cd_path} && /bin/bash checkout.sh' {VERBOSE}")
        if ret != 0:
            return ret
    return 0


def execute_docker_commit(group_name):
    for box_name in os.listdir(group_name):
        if not box_name.startswith('box.'):
            continue
        if not os.path.isdir(os.path.join(group_name, box_name)):
            continue
        if not os.path.isfile(os.path.join(group_name, box_name, 'commit.sh')):
            continue
        print(f'<BOXER> executing [commit.sh] in {group_name}/{box_name}/')
        cd_path = os.path.join(group_name, box_name)
        ret = os.system(f"/bin/bash -c 'cd {cd_path} && /bin/bash commit.sh' {VERBOSE}")
        if ret != 0:
            return ret
    return 0


def execute_docker_push(group_name):
    for box_name in os.listdir(group_name):
        if not box_name.startswith('box.'):
            continue
        if not os.path.isdir(os.path.join(group_name, box_name)):
            continue
        if not os.path.isfile(os.path.join(group_name, box_name, 'push.sh')):
            continue
        print(f'<BOXER> executing [push.sh] in {group_name}/{box_name}/')
        cd_path = os.path.join(group_name, box_name)
        ret = os.system(f"/bin/bash -c 'cd {cd_path} && /bin/bash push.sh' {VERBOSE}")
        if ret != 0:
            return ret
    return 0


def init_group(group_name, containers):
    group_dir = os.path.join(os.getcwd(), group_name)
    if os.path.exists(group_dir):
        print(f'path {group_dir} already exists')
        sys.exit(1)
        return
    os.mkdir(group_dir)
    open(os.path.join(group_dir, 'build.header.yml'), 'w').write(
        """# This file is a header of the "docker-compose.build.yml" file that will be generated by BOXER "build" command.
# Please make sure lines indentation is preserved.
# Modify the source code of this file as per your requirements.

version: '3.1'

services:
""")
    open(os.path.join(group_dir, 'build.footer.yml'), 'w').write(
        """# This file is a footer of the "docker-compose.build.yml" file that will be generated by BOXER "build" command.
# For example, here you could specify a list of shared volumes for your containers network to be used during build stage.
# Please, modify the source code of this file as per your requirements.

""")
    open(os.path.join(group_dir, 'run.header.yml'), 'w').write(
        """# This file is a header of the "docker-compose.run.yml" file that will be generated by BOXER "start" command.
# Please make sure lines indentation is preserved.
# Modify the source code of this file as per your requirements.

version: '3.1'

services:
""")
    open(os.path.join(group_dir, 'run.footer.yml'), 'w').write(
        """# This file is a footer of the "docker-compose.run.yml" file that will be generated by BOXER "start" command.
# For example, here you could specify a list of shared volumes to be used by the containers network.
# Please make sure lines indentation is preserved.
# Modify the source code of this file as per your requirements.
#
#volumes:
#  my_shared_volume_abc:
#  my_shared_volume_xyz:

""")
    for container in containers:
        container_name = container.replace('box.', '')
        container_dir_name = container if container.startswith('box.') else 'box.' + container
        container_dir = os.path.join(group_dir, container_dir_name)
        os.mkdir(container_dir)
        open(os.path.join(container_dir, 'build.yml'), 'w').write(
            f"""# The "build.yml" file represents a single "service" section in the "docker-compose.build.yml" file and will be
# automatically picked up by the BOXER during execution of the "build" command.
#
# Pay attention to the mandatory "container_name" field - the value here is used in other BOXER config files.
#
# Check out another mandatory field "context" - the context of the container "{container_name}" will be switched
# to the folder "{container_dir}" during "build" stage. You can place any additional files & folders there
# and use them in your scripts while building the container image.
#
# Please also make sure lines indentation is preserved.
#
# Modify the source code of this file as per your requirements.
#
#  {container_name}:
#    container_name: build_{container_name}_1
#    build:
#      context: ./box.{container_name}
#    command: >
#      sh -c "sleep 10000"
#    env_file:
#      - ./box.{container_name}/{container_name}.env
#    depends_on:
#      - another_container_abc
#      - another_container_xyz
""")
        open(os.path.join(container_dir, 'run.yml'), 'w').write(
            f"""# The "run.yml" file represents a single "service" section in the "docker-compose.run.yml" file and will be
# automatically picked up by the BOXER during execution of the "start" command.
#
# Please make sure lines indentation is preserved.
#
# Modify the source code of this file as per your requirements.
#
#  {container_name}:
#    image: base-image-to-be-used:image-version
#    command: >
#      sh -c "cd /sample-app-root-folder && ./run-my-container-script.sh"
#    env_file:
#      - ./box.{container_name}/{container_name}.env
#    environment:
#      - SOME_ENV_VARIABLE=my_value_is_here
#    volumes:
#      - my_shared_volume_abc:/my_shared_volume_abc
#    depends_on:
#      - another_container_abc
#      - another_container_xyz
""")
        open(os.path.join(container_dir, 'checkout.sh'), 'w').write(
            f"""#!/bin/bash
#
# The "checkout.sh" file will be executed by the BOXER during "build" stage and is intended
# to prepare all required files of your container inside of the "{container_dir}" folder.
#
# For example you could use GIT to automatically download and update the source code
# of your application here. This way, every time you run the BOXER "build" command
# your docker containers will be automatically refreshed and rebuilt from the most recent code.
#
# Please modify the source code of this file as per your requirements.
#
#if [ ! -d "./app" ]; then
#    git clone https://github.com/my-github-user/my-awesome-app.git ./app
#fi
#
#if [ -d "./app/.git" ]; then
#    cd ./app
#    git fetch
#    git reset --hard
#    cd ..
#fi
""")
        open(os.path.join(container_dir, '.gitignore'), 'w').write(
            """app
""")
        open(os.path.join(container_dir, '.dockerignore'), 'w').write(
            """.git
.pytest_cache
htmlcov
*.pyc
""")
        open(os.path.join(container_dir, 'Dockerfile'), 'w').write(
            f"""# This Dockerfile will be used by the BOXER during "build" stage to build image for container "{container_name}".
#
# Please modify that file as per your requirements or remove it in case container "{container_name}" uses pre-built image.
""")
        open(os.path.join(container_dir, f'{container_name}.env'), 'w').write(
            f"""SOME_ENV_VARIABLE_IN_CONTAINER_{container_name.upper()}=some_value_to_be_there
ANOTHER_ENV_VARIABLE_IN_CONTAINER_{container_name.upper()}=some_another_value
""")
        open(os.path.join(container_dir, 'exec.sh'), 'w').write(
            f"""#!/bin/bash
#
# The "exec.sh" file will be executed by the BOXER during "build" stage and is intended
# to execute (if this is needed) additional scripts after the "docker-compose up" command was completed.
# This way you could apply additional steps during your "build" stage and later commit results into
# the docker cached images.
# Thus, further executions of the BOXER "start" command will be possible and will happen much faster.
#
# For example, you could run database migrations on that stage and then you do not have to apply them
# every time you start all of the containers in the "{group_name}" group.
#
# In case multiple containers need additional scripts to be executed after the "build" stage
# and are dependent on each other, you can control the execution order of those additional scripts.
# To do that, just rename the "exec.sh" file for the first container to "exec-1.sh", then second container's
# "exec.sh" to "exec-2.sh" and so on.
#
# Please modify that file as per your requirements or remove it in case container "{container_name}" do not require
# anything to be executed during the "build" stage.
#
# docker exec -i build_{container_name}_1 sh -c 'cd /app && python manage.py migrate --noinput'
""")
        open(os.path.join(container_dir, 'commit.sh'), 'w').write(
            f"""#!/bin/bash
#
# The "commit.sh" file will be executed by the BOXER during "build" stage and is intended
# to run "docker commit" for the "{container_name}" container.
# This will create a new docker image from the changes made in the docker container during "build" stage.
#
# Please modify that file as per your requirements or remove it in case container "{container_name}" do not require
# anything to be committed during the "build" stage.
#
# docker commit build_{container_name}_1 my-image-{container_name}
""")
        open(os.path.join(container_dir, 'push.sh'), 'w').write(
            f"""#!/bin/bash
#
# The "push.sh" file will be executed by the BOXER during "build" stage and is intended
# to run "docker push" for the "{container_name}" container image.
#
# This will push the result image to the remote repository. This will make possible to
# use that image to start your container group later without building from scratch.
#
# In order this to be working, the corresponding "commit.sh" file must be also correctly configured.
#
# Please modify that file as per your requirements or remove it in case container "{container_name}" do not require
# anything to be pushed to the remote repository.
#
# docker push my-image-{container_name}
""")    
    print(f'<BOXER> network group name is [{group_name}]')
    print(f'<BOXER> target folder is [{group_dir}]')
    print('<BOXER> done')
    return


class CustomArgumentParser(argparse.ArgumentParser):

    def format_help(self):
        return __doc__ + argparse.ArgumentParser.format_help(self)  # @UndefinedVariable


def get_group_name(args):
    global ALIAS
    if not args.group_name:
        print('must provide a name of the target group of containers, use the "--group-name input" argument')
        sys.exit(1)
        return
    group_name = args.group_name
    if not group_name.endswith('.boxes'):
        ALIAS = group_name.lower()
        group_name = group_name + '.boxes'
    else:
        ALIAS = group_name.replace('.boxes').lower()
    return group_name


def main():
    global VERBOSE
    global QUITE_PULL
    global ALIAS

    parser = CustomArgumentParser(
        prog='boxer',
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        '-q', '--quite', dest='quite', action='store_const', const=True, default=False,
    )
    parser.add_argument(
        '-g', '--group-name', dest='group_name',
        help='Name of the target group of containers',
    )
    parser.add_argument(
        '-c', '--container', dest='container',
        help='Name of the target container in the group where the command will be executed',
    )
    parser.add_argument(
        'command',
        default='',
        nargs=argparse.REMAINDER,
        help='A command you are going to execute: init, build, start, exec, stop',
    )

    args = parser.parse_args()

    command = ''
    if args.command:
        command = args.command[0]
    if not command:
        command = 'help'

    if args.quite:
        VERBOSE = '1>boxer_stdout.txt 2>boxer_stderr.txt'
        QUITE_PULL = '--quiet-pull '

    if command == 'help':
        parser.print_help()
        return

    if command == 'init':
        init_parser = argparse.ArgumentParser(
            prog='boxer',
        )
        init_parser.add_argument(
            '-q', '--quite', dest='quite', action='store_const', const=True, default=False,
        )
        init_parser.add_argument(
            '-g', '--group-name', dest='group_name',
            help='Name of the target group of containers',
        )
        init_parser.add_argument(
            'init',
        )
        init_parser.add_argument(
            'container',
            nargs='+',
            action='extend',
            help='Containers names to be added to the group',
        )
        init_args = init_parser.parse_args()

        if not init_args.container:
            print('must provide a name for at least one container to be added to the group')
            sys.exit(1)
            return

        if '-h' == init_args.container[0] or '--help' == init_args.container[0]:
            init_args.print_help()
            return

        group_name = get_group_name(init_args)
        init_group(group_name, init_args.container)
        return

    if command == 'build':
        group_name = get_group_name(args)
        group_dir = os.path.join(os.getcwd(), group_name)
        print(f'<BOXER> network group name is [{group_name}]')
        print(f'<BOXER> target folder is [{group_dir}]')
        generate_docker_compose_build_file(group_name)
        check_ret(execute_docker_compose_build_down(group_name))
        check_ret(execute_checkout(group_name))
        check_ret(execute_docker_compose_build(group_name))
        check_ret(execute_docker_exec(group_name))
        check_ret(execute_docker_commit(group_name))
        check_ret(execute_docker_push(group_name))
        check_ret(execute_docker_compose_build_down(group_name))
        print('<BOXER> done')
        return

    if command == 'start':
        group_name = get_group_name(args)
        group_dir = os.path.join(os.getcwd(), group_name)
        print(f'<BOXER> network group name is [{group_name}]')
        print(f'<BOXER> target folder is [{group_dir}]')
        generate_docker_compose_run_file(group_name)
        check_ret(execute_docker_compose_run(group_name))
        print('<BOXER> done')
        return

    if command == 'stop':
        group_name = get_group_name(args)
        group_dir = os.path.join(os.getcwd(), group_name)
        print(f'<BOXER> network group name is [{group_name}]')
        print(f'<BOXER> target folder is [{group_dir}]')
        check_ret(execute_docker_compose_run_down(group_name))
        print('<BOXER> done')
        return

    if command == 'exec':
        exec_parser = argparse.ArgumentParser(
            prog='boxer',
        )
        exec_parser.add_argument(
            '-q', '--quite', dest='quite', action='store_const', const=True, default=False,
        )
        exec_parser.add_argument(
            '-g', '--group-name', dest='group_name',
            help='Name of the target group of containers',
        )
        exec_parser.add_argument(
            '-c', '--container', dest='container',
            help='Name of the target container in the group where the command will be executed',
        )
        exec_parser.add_argument(
            'exec',
        )
        exec_parser.add_argument(
            'command',
            help='Command and arguments to be executed inside of the target container',
            nargs=argparse.PARSER,
        )
        exec_args = exec_parser.parse_args()
        if exec_args.command:
            if '-h' == exec_args.command[0] or '--help' == exec_args.command[0]:
                exec_parser.print_help()
                return

        group_name = get_group_name(exec_args)
        print(f'<BOXER> network group name is [{group_name}]')
        check_ret(execute_docker_compose_run_exec(group_name, exec_args.container, args.command[1:]))
        print('<BOXER> done')
        return

    parser.print_help()
    return


if __name__ == '__main__':
    main()
