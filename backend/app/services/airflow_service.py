"""
Airflow service for workflow orchestration
Provides DAG management, run monitoring, and statistics
"""

from typing import List, Dict, Any, Optional
import logging
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime, timedelta
from ..core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AirflowService:
    """Service for managing Airflow operations"""

    def __init__(self):
        self.base_url = settings.AIRFLOW_BASE_URL.rstrip('/')
        self.username = settings.AIRFLOW_USERNAME
        self.password = settings.AIRFLOW_PASSWORD
        self.auth = HTTPBasicAuth(self.username, self.password)
        self.api_url = f"{self.base_url}/api/v1"

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to Airflow API"""
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        try:
            response = requests.request(
                method=method,
                url=url,
                auth=self.auth,
                timeout=30,
                **kwargs
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Airflow API request failed: {str(e)}")
            raise

    async def list_dags(
        self,
        limit: int = 100,
        offset: int = 0,
        only_active: bool = True
    ) -> Dict[str, Any]:
        """List all DAGs"""
        try:
            params = {
                'limit': limit,
                'offset': offset,
            }
            if only_active:
                params['only_active'] = 'true'

            response = self._make_request('GET', '/dags', params=params)

            dags = response.get('dags', [])

            # Enrich DAG data with additional info
            enriched_dags = []
            for dag in dags:
                enriched_dag = {
                    'dag_id': dag.get('dag_id'),
                    'description': dag.get('description'),
                    'is_paused': dag.get('is_paused'),
                    'is_active': dag.get('is_active'),
                    'schedule_interval': dag.get('schedule_interval'),
                    'tags': dag.get('tags', []),
                    'owners': dag.get('owners', []),
                    'last_parsed_time': dag.get('last_parsed_time'),
                    'next_dagrun': dag.get('next_dagrun'),
                    'next_dagrun_create_after': dag.get('next_dagrun_create_after'),
                }
                enriched_dags.append(enriched_dag)

            return {
                'dags': enriched_dags,
                'total_entries': response.get('total_entries', len(dags))
            }
        except Exception as e:
            logger.error(f"Error listing DAGs: {str(e)}")
            raise

    async def get_dag(self, dag_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific DAG"""
        try:
            response = self._make_request('GET', f'/dags/{dag_id}')
            return response
        except Exception as e:
            logger.error(f"Error getting DAG {dag_id}: {str(e)}")
            raise

    async def get_dag_runs(
        self,
        dag_id: str,
        limit: int = 25,
        offset: int = 0,
        state: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get DAG runs for a specific DAG"""
        try:
            params = {
                'limit': limit,
                'offset': offset,
            }
            if state:
                params['state'] = state

            response = self._make_request('GET', f'/dags/{dag_id}/dagRuns', params=params)

            dag_runs = response.get('dag_runs', [])

            # Format runs for frontend
            formatted_runs = []
            for run in dag_runs:
                formatted_run = {
                    'dag_run_id': run.get('dag_run_id'),
                    'dag_id': run.get('dag_id'),
                    'state': run.get('state'),
                    'execution_date': run.get('execution_date'),
                    'start_date': run.get('start_date'),
                    'end_date': run.get('end_date'),
                    'external_trigger': run.get('external_trigger'),
                    'conf': run.get('conf'),
                }
                formatted_runs.append(formatted_run)

            return {
                'dag_runs': formatted_runs,
                'total_entries': response.get('total_entries', len(dag_runs))
            }
        except Exception as e:
            logger.error(f"Error getting DAG runs for {dag_id}: {str(e)}")
            raise

    async def trigger_dag(
        self,
        dag_id: str,
        conf: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Trigger a new DAG run"""
        try:
            payload = {
                'conf': conf or {}
            }

            response = self._make_request(
                'POST',
                f'/dags/{dag_id}/dagRuns',
                json=payload
            )

            return {
                'dag_run_id': response.get('dag_run_id'),
                'dag_id': response.get('dag_id'),
                'state': response.get('state'),
                'execution_date': response.get('execution_date'),
            }
        except Exception as e:
            logger.error(f"Error triggering DAG {dag_id}: {str(e)}")
            raise

    async def pause_dag(self, dag_id: str) -> Dict[str, Any]:
        """Pause a DAG"""
        try:
            response = self._make_request(
                'PATCH',
                f'/dags/{dag_id}',
                json={'is_paused': True}
            )
            return response
        except Exception as e:
            logger.error(f"Error pausing DAG {dag_id}: {str(e)}")
            raise

    async def unpause_dag(self, dag_id: str) -> Dict[str, Any]:
        """Unpause a DAG"""
        try:
            response = self._make_request(
                'PATCH',
                f'/dags/{dag_id}',
                json={'is_paused': False}
            )
            return response
        except Exception as e:
            logger.error(f"Error unpausing DAG {dag_id}: {str(e)}")
            raise

    async def get_task_instances(
        self,
        dag_id: str,
        dag_run_id: str
    ) -> List[Dict[str, Any]]:
        """Get task instances for a specific DAG run"""
        try:
            response = self._make_request(
                'GET',
                f'/dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances'
            )

            task_instances = response.get('task_instances', [])

            # Format for frontend
            formatted_tasks = []
            for task in task_instances:
                formatted_task = {
                    'task_id': task.get('task_id'),
                    'state': task.get('state'),
                    'start_date': task.get('start_date'),
                    'end_date': task.get('end_date'),
                    'duration': task.get('duration'),
                    'try_number': task.get('try_number'),
                    'max_tries': task.get('max_tries'),
                }
                formatted_tasks.append(formatted_task)

            return formatted_tasks
        except Exception as e:
            logger.error(f"Error getting task instances: {str(e)}")
            raise

    async def get_task_logs(
        self,
        dag_id: str,
        dag_run_id: str,
        task_id: str,
        try_number: int = 1
    ) -> str:
        """Get logs for a specific task instance"""
        try:
            response = self._make_request(
                'GET',
                f'/dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances/{task_id}/logs/{try_number}'
            )
            return response.get('content', '')
        except Exception as e:
            logger.error(f"Error getting task logs: {str(e)}")
            raise

    async def get_statistics(self) -> Dict[str, Any]:
        """Get overall Airflow statistics"""
        try:
            # Get all DAGs
            all_dags = await self.list_dags(limit=1000, only_active=False)
            total_dags = all_dags['total_entries']
            active_dags = len([d for d in all_dags['dags'] if d['is_active']])
            paused_dags = len([d for d in all_dags['dags'] if d['is_paused']])

            # Get recent DAG runs across all DAGs
            # We'll need to aggregate this from individual DAGs
            recent_runs = {
                'running': 0,
                'success': 0,
                'failed': 0,
                'queued': 0
            }

            # Sample recent runs from first few DAGs
            for dag in all_dags['dags'][:10]:  # Check first 10 DAGs for stats
                try:
                    runs = await self.get_dag_runs(dag['dag_id'], limit=10)
                    for run in runs['dag_runs']:
                        state = run['state']
                        if state == 'running':
                            recent_runs['running'] += 1
                        elif state == 'success':
                            recent_runs['success'] += 1
                        elif state == 'failed':
                            recent_runs['failed'] += 1
                        elif state == 'queued':
                            recent_runs['queued'] += 1
                except:
                    continue

            return {
                'total_dags': total_dags,
                'active_dags': active_dags,
                'paused_dags': paused_dags,
                'recent_runs': recent_runs,
                'running_tasks': recent_runs['running'],
                'success_rate': (
                    round(recent_runs['success'] / max(1, sum(recent_runs.values())) * 100, 2)
                )
            }
        except Exception as e:
            logger.error(f"Error getting statistics: {str(e)}")
            raise

    async def get_health(self) -> Dict[str, Any]:
        """Check Airflow health"""
        try:
            response = self._make_request('GET', '/health')
            return {
                'status': 'healthy' if response else 'unhealthy',
                'metadatabase': response.get('metadatabase', {}).get('status'),
                'scheduler': response.get('scheduler', {}).get('status'),
            }
        except Exception as e:
            logger.error(f"Error checking health: {str(e)}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }


# Singleton instance
_airflow_service = None

def get_airflow_service() -> AirflowService:
    """Get or create Airflow service instance"""
    global _airflow_service
    if _airflow_service is None:
        _airflow_service = AirflowService()
    return _airflow_service
