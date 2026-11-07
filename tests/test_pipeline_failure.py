import pytest
import main


def test_pipeline_stops_when_ingestion_fails(monkeypatch):

    storage_called = False

    # Simulate a missing source file
    def simulate_ingestion_failure():

        raise FileNotFoundError(
            "Simulated missing source file"
        )

    # Track whether database storage gets called
    def track_database_storage(*args, **kwargs):

        nonlocal storage_called

        storage_called = True

    # Replace actual functions with test functions
    monkeypatch.setattr(
        main,
        "load_all_sources",
        simulate_ingestion_failure
    )

    monkeypatch.setattr(
        main,
        "save_to_database",
        track_database_storage
    )

    # Verify that the pipeline reports the failure
    with pytest.raises(FileNotFoundError):

        main.main()

    # Database storage must not execute after ingestion fails
    assert storage_called is False