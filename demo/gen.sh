#! /bin/bash

is_mac() { [[ $OSTYPE == darwin14* ]]; }
is_linux() { [[ $OSTYPE == linux* ]]; }

if is_mac; then
    python apikit.py --api demo/api.api --lang android --dir /Users/feng/workspace/android-test/app/src/main/java --context /api --ns com.kanzhun.api
    python apikit.py --api demo/api.api --lang servlet --dir /Users/feng/workspace/server-test/src/main/java --context /api --ns com.kanzhun.api
    python apikit.py --api demo/api.api --lang swift --dir /Users/feng/Desktop/workspace/http/http --context /api --ns ''
    python apikit.py --api demo/api.api --lang objc --dir /Users/feng/Desktop/workspace/httpobc/httpobc/gen --context /api --ns 'Ak'
    python apikit.py --api demo/api.api --lang js --dir /tmp/what.js --context /api --ns ''
fi

if is_linux; then
    python apikit.py --api demo/api.api --lang android --dir /home/feng/AndroidStudioProjects/MyApplication/app/src/main/java/ --context /api --ns com.kanzhun.api
    python apikit.py --api demo/api.api --lang servlet --dir /home/feng/workspace/server-test/src/main/java/ --context /api --ns com.kanzhun.api
    python apikit.py --api demo/api.api --lang swift --dir /tmp/swift --context /api --ns ''
    python apikit.py --api demo/api.api --lang objc --dir /tmp/objc --context /api --ns 'Ak'
    python apikit.py --api demo/api.api --lang js --dir /tmp/what.js --context /api --ns ''
fi
