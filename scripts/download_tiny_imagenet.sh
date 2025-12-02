#!/bin/bash
kaggle datasets download akash2sharma/tiny-imagenet -p ./data --unzip && \
    rm -rf ./data/tiny-imagenet-200/tiny-imagenet-200  # there is a duplicate folder inside