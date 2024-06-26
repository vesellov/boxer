from setuptools import setup, find_packages

setup_params = dict(
    name='boxer',
    version='1.0.0',
    author='Veselin Penev',
    author_email='penev.veselin@gmail.com',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    scripts=['bin/boxer', ],
    description='The BOXER tool automates and facilitate testing of your dockerized multi-component application',
    long_description=(
        "This tool automates and facilitate testing of your dockerized multi-component application."
        ""
        "Involving 'docker-compose', the 'boxer' script helps you to create an isolated docker network"
        "that simulates real-time execution of your dockerized application."
        ""
        "The 'boxer' tool generates a docker-compose YAML file for you based on your pre-configurations"
        "and then with a single command you spawn a running real-time environment where each component"
        "is already initialized and they are all interconnected nicely with each other and isolated."
        ""
        "Additional component is usually added to the docker-compose network to be able to orchestrate"
        "behavior of your application and later verify the outcome and thus test your multi-component application."
        "The orchestrator container can use for example 'pytest' or 'robotframework' to define a set"
        "of tests that you may want to automate as part of your CI/CD."
        ""
        "Using the boxer tool involves the following steps:"
        "    init    Generates initial setup with all files and sub-folders for your new simulation"
        "    build   This will build all of the containers and cache locally the docker images"
        "    start   Will spawn all of the containers in the target network group from cached docker images"
        "    exec    Executes a command via shell inside of one of the running containers"
        "    stop    Terminates all running containers in the target network group"
    ),
    url='https://github.com/kpn/boxer',
    install_requires=[],
)

def run_setup():
    setup(**setup_params)

if __name__ == '__main__':
    run_setup()
