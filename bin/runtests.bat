@ECHO off

SET test=crawlmi
SET PYTHONPATH=%CD%
IF NOT "%1" == "" SET test="%1"
trial.py %test%
