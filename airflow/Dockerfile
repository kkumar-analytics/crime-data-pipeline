FROM astrocrpublic.azurecr.io/runtime:3.0-1

RUN pip install astronomer-cosmos[dbt.all]
# install dbt into a venv to avoid package dependency conflicts
WORKDIR "/usr/local/airflow"
COPY dbt-requirements.txt ./
RUN python -m virtualenv dbt_venv && source dbt_venv/bin/activate && \
    pip install --no-cache-dir -r dbt-requirements.txt && deactivate