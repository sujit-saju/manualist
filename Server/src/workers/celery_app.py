"""Celery entry point for the ingestion worker."""

from os import environ

from celery import Celery  # type: ignore[import-untyped]

app = Celery("manualist", broker=environ.get("REDIS_URL"))
