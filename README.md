# equipment-availability-service

Equipment Availability Service for Drupal

## Purpose

Flask microservice for retrieving Equipment Availability information from
the Alma API, based on requests from Drupal.

## Development Environment

Python version: 3.12

### Installation

```zsh
git clone git@github.com:umd-lib/equipment-availability-service.git
cd equipment-availability-service
pyenv install --skip-existing $(cat .python-version)
python -m venv .venv --prompt equipment-availability
source .venv/bin/activate
pip install -r requirements.test.txt -e .
```

### Configuration

1) Copy the "env-template" file to ".env"

```zsh
cp env-template .env
```

2) Edit the file

```zsh
vi .env
```

and make the following changes:

* Enter a value for the "ALMA_API_KEY":
* (Optional) Uncomment the `FLASK_DEBUG=1` to run the application in debug mode
```

### Running

To run the application in debug mode, with hot code reloading:

```zsh
flask --app "equipment_availability.web:app(config='alma_config.yaml')" run
```

The microservice will be available at <http://localhost:5000/>,
with a simple HTML landing page.

To change the port, add `-p {port number}` to the `flask` command:

```zsh
# for example, to run on port 8000
flask --app "equipment_availability.web:app(config='alma_config.yaml')" run -p 8000
```

### Testing

This project uses the [pytest] testing framework. To run the full
[test suite](tests):

```zsh
pytest
```

To run the test suite with coverage information from [pytest-cov]:

```zsh
pytest --cov src --cov-report term-missing
```

This project also uses [pycodestyle] as a style checker and linter:

```zsh
pycodestyle .
```

Configuration of pycodestyle is found in the [tox.ini](tox.ini) file.

### Using VSCode Dev Containers

This repo has been configured to use VSCode's Development Containers.
Upon opening this codebase in VSCode:

* A notification will pop up asking if the folder should be re-opened in a
  container. Select "Yes". VS Code will restart and create a Docker container
  (this takes a minute or two, if the Docker image has not previously been
  downloaded).

* The pip install command is run as part of the Docker container setup, and
  various VS Code extensions are automatically added.

* To run the microservice and Python tools such as "pytest", open a terminal in
  VS Code (select "Terminal | New Terminal") from the menubar.

### Deploying using Docker

Build the image:

```zsh
docker build -t docker.lib.umd.edu/equipment-availability-service:latest .
```

If you need to build for multiple architectures (e.g., AMD and ARM), you
can use `docker buildx`. This assumes you have a builder named "local"
configured for use with your docker buildx system, and you are logged in
to a Docker repository that you can push images to:

```zsh
docker buildx build --builder local --platform linux/amd64,linux/arm64 \
    -t docker.lib.umd.edu/equipment-availability-service:latest --push .

# then pull the image so it is available locally
docker pull docker.lib.umd.edu/equipment-availability-service:latest
```

Run the container:

```zsh
export ALMA_API_KEY=<Alma API Key>
docker run --publish 5000:5000 --env ALMA_API_KEY=$ALMA_API_KEY docker.lib.umd.edu/equipment-availability:latest --alma_config=alma_config.yaml
```

If you created a `.env` file (see [Configuration](#configuration)), you
can run the Docker image using that file.

```zsh
docker run -p 5000:5000 \
    --env-file .env \
    docker.lib.umd.edu/equipment-availability:latest --alma_config=alma_config.yaml
```

[pytest]: https://docs.pytest.org/en/7.3.x/
[pytest-cov]: https://pypi.org/project/pytest-cov/
[pycodestyle]: https://pycodestyle.pycqa.org/en/latest/
