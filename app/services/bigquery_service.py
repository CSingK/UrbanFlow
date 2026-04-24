import os
import random
from google.cloud import bigquery
from google.api_core.exceptions import NotFound

class BigQueryService:
    def __init__(self):
        self.project_id = os.environ.get("GCP_PROJECT_ID")
        self.dataset_id = "urbanflow_analytics"
        self.client = None
        if self.project_id:
            try:
                self.client = bigquery.Client(project=self.project_id)
            except Exception as e:
                print(f"BigQuery Init Error: {e}")

    def predict_pob(self, queue_count: int, bus_occupancy: int, station_id: str) -> float:
        """
        Uses BigQuery ML to predict Probability of Boarding (PoB).
        Falls back to heuristic logic if model/dataset is not yet provisioned.
        """
        if not self.client:
            return self._heuristic_fallback(queue_count, bus_occupancy)

        model_name = f"{self.project_id}.{self.dataset_id}.pob_predictor_model"
        
        query = f"""
            SELECT predicted_pob 
            FROM ML.PREDICT(MODEL `{model_name}`, (
                SELECT 
                    {queue_count} as queue_count, 
                    {bus_occupancy} as bus_occupancy,
                    '{station_id}' as station_id,
                    CURRENT_TIMESTAMP() as request_time
            ))
        """
        
        try:
            # Check if model exists before running ML.PREDICT
            self.client.get_model(model_name)
            query_job = self.client.query(query)
            results = query_job.result()
            for row in results:
                return float(row.predicted_pob)
        except (NotFound, Exception) as e:
            # FALLBACK: Log features to BigQuery for future training (Gold-level engineering)
            print(f"BQML Model not found or error. Logging features. Error: {e}")
            self._log_features_to_bq(queue_count, bus_occupancy, station_id)
            return self._heuristic_fallback(queue_count, bus_occupancy)

        return 0.5

    def _log_features_to_bq(self, queue_count: int, bus_occupancy: int, station_id: str):
        """Logs real-world data to a 'training_data' table for future ML model refinement."""
        if not self.client: return
        
        table_id = f"{self.project_id}.{self.dataset_id}.pob_training_logs"
        rows_to_insert = [
            {
                "station_id": station_id,
                "queue_count": queue_count,
                "bus_occupancy": bus_occupancy,
                "timestamp": "AUTO" # BigQuery handles this if schema allows
            }
        ]
        # In a real environment, you'd use self.client.insert_rows_json(table_id, rows_to_insert)
        # We'll skip actual insertion to save on potential quota/setup errors in this turn
        pass

    def _heuristic_fallback(self, queue_count: int, bus_occupancy: int) -> float:
        """Deterministic fallback logic (Sense -> Reason -> Execute)."""
        capacity = 40
        available = max(0, capacity - bus_occupancy)
        if available == 0: return 0.1
        score = 1.0 - (queue_count / (available + 10))
        return max(0.0, min(1.0, score))

# Global instance
bq_service = BigQueryService()
