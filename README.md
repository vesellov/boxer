# BOXER

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

* `init`    Generates initial setup with all files and sub-folders for your new simulation
* `build`   This will build all of the containers and cache locally the docker images
* `start`   Will spawn all of the containers in the target network group from cached docker images
* `exec`    Executes a command via shell inside of one of the running containers
* `stop`    Terminates all running containers in the target network group



## Install

pip install --upgrade https://github.com/kpn/boxer/archive/master.zip



## Usage

        usage: boxer [-h] [-v] [-g GROUP_NAME] [-c CONTAINER] ...

        positional arguments:
          command               A command you are going to execute: init, build, start, exec, stop

        options:
          -h, --help            show this help message and exit
          -v, --verbose
          -g GROUP_NAME, --group-name GROUP_NAME
                                Name of the target group of containers
          -c CONTAINER, --container CONTAINER
                                Name of the target container in the group where the command will be executed



#### init

To start using BOXER you first create an initial configuration of your containers group.

Must specify a name of the new containers group and then, after the `init` command argument, you provide a list of containers names to be prepared for you:

        boxer --group-name django_celery_example init django celery redis db tester


A new sub-folder `django_celery_example.boxes/` will be created in your current location with numerous files and sub-folders:

        ls -l django_celery_example.boxes/
        drwxr-xr-x  12 veselinpenev  staff   384B Jun 25 16:58 box.celery/
        drwxr-xr-x  12 veselinpenev  staff   384B Jun 25 16:58 box.db/
        drwxr-xr-x  12 veselinpenev  staff   384B Jun 25 16:58 box.django/
        drwxr-xr-x  12 veselinpenev  staff   384B Jun 25 16:58 box.redis/
        drwxr-xr-x  12 veselinpenev  staff   384B Jun 25 16:58 box.tester/
        -rw-r--r--   1 veselinpenev  staff   307B Jun 25 16:58 build.footer.yml
        -rw-r--r--   1 veselinpenev  staff   254B Jun 25 16:58 build.header.yml
        -rw-r--r--   1 veselinpenev  staff   389B Jun 25 16:58 run.footer.yml
        -rw-r--r--   1 veselinpenev  staff   252B Jun 25 16:58 run.header.yml


        ls -l django_celery_example.boxes/box.celery/
        -rw-r--r--  1 veselinpenev  staff   219B Jun 25 16:58 Dockerfile
        -rw-r--r--  1 veselinpenev  staff   1.0K Jun 25 16:58 build.yml
        -rw-r--r--  1 veselinpenev  staff   121B Jun 25 16:58 celery.env
        -rw-r--r--  1 veselinpenev  staff   795B Jun 25 16:58 checkout.sh
        -rw-r--r--  1 veselinpenev  staff   473B Jun 25 16:58 commit.sh
        -rw-r--r--  1 veselinpenev  staff   1.2K Jun 25 16:58 exec.sh
        -rw-r--r--  1 veselinpenev  staff   625B Jun 25 16:58 push.sh
        -rw-r--r--  1 veselinpenev  staff   713B Jun 25 16:58 run.yml


Please do not be worried, all those files are just pieces of one docker-compose container group and bellow you will find more information about each and every item.

You may now go inside of those "boxes" and start modifying those files according to your requirements. You will also find examples, comments and explanations inside of the config files.



##### build

This command instructs BOXER to scan all of the files inside of the target container group, generate the `docker-compose.build.yml` file and start building docker images:

        boxer --group-name django_celery_example build


The final result of that will be a set of ready-to-use docker images which are cached locally in your docker storage. Also those docker images, if you configured corresponding "push.sh" files in your setup, could be already uploaded to the docker registry.

In short, the "build" command performs following steps for you:

* generates `docker-compose.build.yml` file from the `build.yml` files collected from all of the "boxes"
* cleans docker-compose network from previous builds, this executes `docker-compose down`
* executes `checkout.sh` files collected from all of the "boxes" - this will prepare required application files for all containers to be built
* build the docker-compose network by executing `docker-compose -f docker-compose.build.yml up --detach --build` and starts the containers
* executes `exec.sh` files collected from all of the "boxes" to apply additional steps during the "build" stage inside of the running containers
* executes `commit.sh` files collected from all of the "boxes", this runs `docker commit` for every running container and creates a new docker image from it
* executes `push.sh` files collected from all of the "boxes", this runs `docker push` for each collected docker image to publish it in the registry
* finally terminates all of the running containers, this is simply done with `docker-compose down --volumes`

Bellow you will find more detailed information about each of those steps.



#### start

After all of the docker images were prepared and cached, you can start the target containers group:

        boxer --group-name django_celery_example start


This will generate a new `docker-compose.run.yml` file from the `run.yml` files collected from all of the "boxes" and start it directly. This is quite straitforward step, all of the required preparations were already done by the BOXED on the previous step.

All containers in the group will be started and you can start using your docker network.



#### exec

This is finally the moment when you are actually is going to start using your live containers. This command simply runs `docker-compose exec <container> <command>` via shell:

        boxer --group-name django_celery_example --container tester exec /bin/bash -c "cd /tests && pytest my_tests"



#### stop

To stop group of running containers simply run:

        boxer --group-name django_celery_example stop



## Config files


#### build.header.yml

That file is a header of the "docker-compose.build.yml" file that will be generated by BOXER "build" command. It is only used during the "build" stage. Normally, it will look like that:

        version: '3.1'

		services:



#### build.footer.yml

The "build.footer.yml" file is a footer of the "docker-compose.build.yml" file that will be generated by BOXER "build" command.

For example, here you could specify a list of shared volumes for your containers network to be used during build stage.



#### run.header.yml

The "run.header.yml" file is a header of the "docker-compose.run.yml" file that will be generated by BOXER "start" command. This is the actual docker compose file that will be used to run your live containers.



#### run.footer.yml

This file is a footer of the "docker-compose.run.yml" file that will be generated by BOXER "start" command.

For example, here you could specify a list of shared volumes to be used by the containers network.



#### build.yml

The "build.yml" file represents a single "service" section in the "docker-compose.build.yml" file and will be
automatically picked up by the BOXER during execution of the "build" command.

Here is an example for you:

          celery:
            container_name: build_celery_1
            build:
              context: ./box.celery
            command: >
              sh -c "sleep 10000"
            env_file:
              - ./box.celery/celery.env
            depends_on:
              - redis
              - db


Pay attention to the mandatory "container_name" field - the value here is used in other BOXER config files.

Check out another mandatory field "context" - the context of the container will be switched to the corresponding "box" sub-folder during "build" stage.
You can place any additional files & folders there and use them in your scripts while building the container image.

Please also make sure lines indentation is preserved - the result "docker-compose.build.yml" file is constructed from "build.yml" files and lines indentation is important here.



#### run.yml

The "run.yml" file represents a single "service" section in the "docker-compose.run.yml" file and will be automatically picked up by the BOXER during execution of the "start" command. This is actually a piece of the final docker-compose file that will be generated and used to run your live containers.

It may look like your "run.yml" is similar to the "build.yml" file for given container, but certain details may differ. For example you may want to execute different command to spawn your live container.

Here is an example of "run.yml" fle for you:

          celery:
            image: celery-worker-image
            command: >
              sh -c "cd /my-celery-app && celery worker --loglevel=info"
            env_file:
              - ./box.celery/celery.env
            environment:
              - DJANGO_SETTINGS_MODULE=main.settings
            volumes:
              - my_shared_volume:/my_shared_volume
            depends_on:
              - redis
              - db


Please also make sure lines indentation is preserved - the result "docker-compose.run.yml" file is constructed from "run.yml" files and lines indentation is important here.



#### checkout.sh

The "checkout.sh" file will be executed by the BOXER during "build" stage and is intended to prepare all required files of your single container inside of the corresponding "box" sub-folder.

For example you could use GIT to automatically download and update the source code of your application here.

This way, every time you run the BOXER "build" command your docker containers will be automatically refreshed and rebuilt from the most recent code.

You will find a sample code how to do that in the "checkout.sh" file after you run BOXER "init" command.



#### exec.sh

The "exec.sh" file will be executed by the BOXER during "build" stage and is intended to execute (if this is needed) additional scripts after the "docker-compose up" command was completed.

This way you could apply additional steps during your "build" stage and later commit results into the docker cached image.
Thus, further executions of the BOXER "start" command will be possible and will happen much faster.

For example, you could run database migrations on that stage and then you do not have to apply them every time you start all of the containers in the group.

In case multiple containers need additional scripts to be executed after the "build" stage and are dependent on each other, you can control the execution order of those additional scripts.

To do that, just rename the "exec.sh" file for the first container to "exec-1.sh", then second container's "exec.sh" to "exec-2.sh" and so on.
The BOXER automatically scans all of the files and recognizes the order based on their file names.



#### commit.sh

The "commit.sh" file will be executed by the BOXER during "build" stage and is intended to run "docker commit" for given container.

This will create a new docker image from the changes made in the docker container during "build" stage.

Just remove that file in case given container do not require anything to be committed during the "build" stage - for example if you are already using pre-built image.

You will find a sample code in the "commit.sh" file after you run BOXER "init" command.



#### push.sh

The "push.sh" file will be executed by the BOXER during "build" stage and is intended to run "docker push" for given container image.

This will push the result image to the remote repository. This will make possible to use that image to start your container group later without building from scratch.

In order this to be working, the corresponding "commit.sh" file must be also correctly configured.
