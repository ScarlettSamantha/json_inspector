python -m pip install --upgrade pip
python -m pip install -r requirements.txt
briefcase update --update-support --update-stub --update-resources --update-requirements
briefcase build windows
briefcase package windows --adhoc-sign