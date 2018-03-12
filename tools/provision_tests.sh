#!/bin/bash

### Folk RNN WebApp functional / unit test requirements, for dev only

echo ***
echo *** Check Folk RNN Test Rig
echo ***

# Selenium for Python
pip3.6 install "selenium<4"

# Chrome and Selenium ChromeDriver (to be used headless)
if [ ! -f /usr/local/bin/chromedriver ]; then
    apt-get install --yes chromium-browser
    apt-get install --yes unzip
    apt-get install --yes libgconf-2-4
    wget --no-verbose https://chromedriver.storage.googleapis.com/2.33/chromedriver_linux64.zip
    unzip chromedriver*
    chmod +x chromedriver
    mv chromedriver /usr/local/bin/chromedriver
    rm chromedriver*
fi