rm ./wheels/*.whl

pip3.11 download -r requirements.txt --dest ./wheels --only-binary=:all: --python-version=3.11
pip3.11 download -r requirements.txt --dest ./wheels --only-binary=:all: --python-version=3.11 --platform=macosx_11_0_arm64
pip3.11 download -r requirements.txt --dest ./wheels --only-binary=:all: --python-version=3.11 --platform=macosx_12_0_x86_64
pip3.11 download -r requirements.txt --dest ./wheels --only-binary=:all: --python-version=3.11 --platform=win_amd64

pip3.11 download -r requirements-nodeps.txt --no-deps --dest ./wheels --only-binary=:all: --python-version=3.11
pip3.11 download -r requirements-nodeps.txt --no-deps --dest ./wheels --only-binary=:all: --python-version=3.11 --platform=macosx_11_0_arm64
pip3.11 download -r requirements-nodeps.txt --no-deps --dest ./wheels --only-binary=:all: --python-version=3.11 --platform=macosx_12_0_x86_64
pip3.11 download -r requirements-nodeps.txt --no-deps --dest ./wheels --only-binary=:all: --python-version=3.11 --platform=win_amd64

echo "LIST OF WHEELS:\n"
find ./wheels | sort

/opt/blender/4.2/blender --command extension build --split-platforms --output-dir=..

/opt/blender/4.3/blender --command extension install-file -r user_default ../audvis-6.0.0-linux_x64.zip 
/opt/blender/4.3/blender
