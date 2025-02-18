#! /bin/bash

exit_on_error () {
  echo Executing: $cmd
  echo `$cmd`
  if [ $? -eq 0 ]
  then
    return 0
  else
    echo "Failed to execute $cmd" >&2
    exit 1
  fi
}

cmd="git stash -m WIP"
exit_on_error
cmd="git checkout master"
exit_on_error
cmd="git fetch upstream"
exit_on_error
cmd="git reset --hard upstream/master"
exit_on_error
cmd="git push"
exit_on_error
cmd="git stash pop"
exit_on_error

poetry install
