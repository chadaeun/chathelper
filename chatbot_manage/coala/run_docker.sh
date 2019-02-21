#!/usr/bin/env bash
nvidia-docker run --entrypoint=bash \
-v ./:/coala \
--name coala -it coala:latest --rm
