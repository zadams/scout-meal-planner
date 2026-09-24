#!/usr/bin/env python3
"""Deprecated entry point, kept so old commands keep working.

A single-meal profile (no "meals" list) is planned as a sandwich lunch by
plan_trip.py, which now holds all the logic. Use plan_trip.py directly.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plan_trip  # noqa: E402

if __name__ == "__main__":
    plan_trip.main()
