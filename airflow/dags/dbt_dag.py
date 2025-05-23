"""
Airflow DAG to orchestrate a full dbt pipeline using Astro CLI-integrated containers.
Steps include installing dbt dependencies, seeding, snapshots, source freshness check,
model runs, tests, Elementary data quality run, and publishing reports to GCS.
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
import pendulum
import subprocess
import logging
import os

# Default DAG arguments
default_args = {
    'owner': 'lapd_crime_project',
    'retries': 0
}

def run_dbt_command(command):
    """
    Runs a specified dbt CLI command inside the containerized environment.
    Args:
        command (list): The dbt command to run, e.g., ['dbt', 'run']
    """
    log = logging.getLogger(__name__)
    log.info(f"Running dbt command: {' '.join(command)}")

    try:
        env = os.environ.copy()
        venv_bin_path = '/usr/local/airflow/dbt_venv/bin'
        command[0] = os.path.join(venv_bin_path, 'dbt')  # Override with venv path

        result = subprocess.run(
            command,
            cwd=env.get('DBT_WORKING_DIR', '/usr/local/airflow/dbt/lapd_crime_project'),
            capture_output=True,
            text=True,
            check=True
        )
        log.info(f"dbt command output:\n{result.stdout}")
    except subprocess.CalledProcessError as e:
        log.error(f"dbt command failed: {e.cmd}\nSTDOUT:\n{e.stdout}\nSTDERR:\n{e.stderr}")


# Individual dbt step wrappers
def run_dbt_deps():
    """Install dbt package dependencies."""
    run_dbt_command(['dbt', 'deps'])


def run_dbt_seed():
    """Load seed data into the warehouse."""
    run_dbt_command(['dbt', 'seed'])


def run_dbt_snapshot():
    """Run snapshot logic for slowly changing dimensions."""
    run_dbt_command(['dbt', 'snapshot'])


def run_dbt_source_freshness():
    """Check freshness of dbt sources."""
    run_dbt_command(['dbt', 'source', 'freshness'])


def run_dbt_run():
    """Run all dbt models."""
    run_dbt_command(['dbt', 'run'])


def run_dbt_test():
    """Run all dbt tests."""
    run_dbt_command(['dbt', 'test'])


def run_dbt_elementary():
    """Run Elementary data quality checks."""
    run_dbt_command(['dbt', 'run', '--select', 'elementary'])


def run_dbt_docs_generate():
    """Generate dbt documentation site."""
    run_dbt_command(['dbt', 'docs', 'generate'])


def send_edr_report_to_gcs():
    """
    Use Elementary's `edr` CLI to send the data quality report to a GCS bucket.
    Requirements:
        - edr CLI installed in virtual environment
        - Valid Google service account JSON file
    """
    log = logging.getLogger(__name__)
    log.info("Sending EDR report to GCS using edr send-report")

    try:
        env = os.environ.copy()
        venv_bin_path = '/usr/local/airflow/dbt_venv/bin'
        command = [
            os.path.join(venv_bin_path, 'edr'),
            'send-report',
            '--google-service-account-path',
            '/usr/local/airflow/dq_writer.json',
            '--gcs-bucket-name',
            'lapd-elementary-report'
        ]
        result = subprocess.run(
            command,
            cwd=env.get('DBT_WORKING_DIR', '/usr/local/airflow/dbt/lapd_crime_project'),
            capture_output=True,
            text=True,
            check=True
        )
        log.info(f"edr send-report output:\n{result.stdout}")
    except subprocess.CalledProcessError as e:
        log.error(f"edr send-report failed: {e.cmd}\nSTDOUT:\n{e.stdout}\nSTDERR:\n{e.stderr}")


def upload_dbt_docs_to_gcs():
    """
    Uploads dbt-generated documentation (`target/` folder) to a specified GCS bucket.
    Uses Google Cloud Storage Python client with a service account for authentication.
    """
    from google.cloud import storage

    log = logging.getLogger(__name__)
    bucket_name = 'lapd-elementary-report'
    source_dir = '/usr/local/airflow/dbt/lapd_crime_project/target'
    destination_blob_prefix = 'dbt_docs/'

    try:
        storage_client = storage.Client.from_service_account_json('/usr/local/airflow/dq_writer.json')
        bucket = storage_client.bucket(bucket_name)

        for root, _, files in os.walk(source_dir):
            for file_name in files:
                local_path = os.path.join(root, file_name)
                relative_path = os.path.relpath(local_path, source_dir)
                blob_path = os.path.join(destination_blob_prefix, relative_path)
                blob = bucket.blob(blob_path)
                blob.upload_from_filename(local_path)
                log.info(f"Uploaded {local_path} to gs://{bucket_name}/{blob_path}")
    except Exception as e:
        log.error(f"Failed to upload dbt docs to GCS: {str(e)}")


# Define the DAG
with DAG(
        dag_id='dbt_run',
        default_args=default_args,
        description='Run dbt workflow: seed, snapshot, source freshness, run, and test',
        schedule=None,  # Trigger manually or via external scheduler
        start_date=pendulum.now().subtract(days=1),
        catchup=False,
        tags=['dbt']
) as dag:
    # Task definitions
    deps_task = PythonOperator(task_id='dbt_deps', python_callable=run_dbt_deps)
    seed_task = PythonOperator(task_id='dbt_seed', python_callable=run_dbt_seed)
    snapshot_task = PythonOperator(task_id='dbt_snapshot', python_callable=run_dbt_snapshot)
    source_freshness_task = PythonOperator(task_id='dbt_source_freshness', python_callable=run_dbt_source_freshness)
    run_task = PythonOperator(task_id='dbt_run', python_callable=run_dbt_run)
    test_task = PythonOperator(task_id='dbt_test', python_callable=run_dbt_test)
    elementary_task = PythonOperator(task_id='dbt_elementary_run', python_callable=run_dbt_elementary)
    send_edr_report_to_gcs = PythonOperator(task_id='send_edr_report_to_gcs', python_callable=send_edr_report_to_gcs)
    generate_docs_task = PythonOperator(task_id='dbt_docs_generate', python_callable=run_dbt_docs_generate)
    upload_docs_task = PythonOperator(task_id='upload_dbt_docs_to_gcs', python_callable=upload_dbt_docs_to_gcs)

    # DAG task sequence
    deps_task >> seed_task >> snapshot_task >> source_freshness_task >> run_task >> test_task >> elementary_task >> send_edr_report_to_gcs >> generate_docs_task >> upload_docs_task
