#!/usr/bin/env bash
set -euo pipefail
variant="${1:?base or build}"
[[ "$variant" = base || "$variant" = build ]]
test "$( . /etc/os-release; echo "$VERSION_ID")" = 24.04
python -c 'import sys, ssl, sqlite3, ctypes, bz2, lzma, zlib; assert sys.version_info[:2] == (3,12); assert ssl.get_default_verify_paths().cafile'
python -m pip --version
python -m venv /tmp/test-venv
/tmp/test-venv/bin/python -m pip --version
# Generate a wheel with stdlib, install offline, import and execute it.
python /tests/wheel.py
/tmp/test-venv/bin/pip install --no-index /tmp/smoke_pkg-1.0-py3-none-any.whl
/tmp/test-venv/bin/python -c 'import smoke_pkg; assert smoke_pkg.answer() == 42'
node -e 'const assert=require("node:assert");assert.equal(process.versions.node.split(".")[0],"24"); assert.equal(require("node:crypto").createHash("sha256").update("ok").digest("hex").length,64)'
npm --version
mkdir /tmp/npm-smoke
cd /tmp/npm-smoke
cat > package.json <<'EOF'
{"name":"smoke","version":"1.0.0","scripts":{"test":"node -e \"process.exit(0)\""}}
EOF
npm install --offline --ignore-scripts --no-audit --no-fund
npm test
java -XshowSettings:properties -version 2>&1 | tee /tmp/java-version
grep -q 'java.vendor = Eclipse Adoptium' /tmp/java-version
javac -version 2>&1 | grep -E '^javac 21[.]'
for tool in jar javadoc jdeps jlink jmod jcmd jdb jshell; do command -v "$tool"; done
cd /tmp
cat > Smoke.java <<'EOF'
import java.awt.image.BufferedImage;
import javax.imageio.ImageIO;
import java.io.File;
public class Smoke {
  public static void main(String[] args) throws Exception {
    if (Runtime.version().feature() != 21) throw new AssertionError();
    ImageIO.write(new BufferedImage(2,2,BufferedImage.TYPE_INT_RGB),"png",new File("/tmp/smoke.png"));
    System.out.println("java-ok");
  }
}
EOF
javac Smoke.java
java -Djava.awt.headless=true Smoke | grep java-ok
jar --create --file smoke.jar Smoke.class
jar --list --file smoke.jar | grep Smoke.class
javadoc -quiet -d /tmp/javadoc Smoke.java
# Prove dynamic apt installation/removal, not just presence of the command.
apt-get update
apt-get install -y --no-install-recommends jq
jq -ne '1+1 == 2'
apt-get purge -y jq
if [[ "$variant" = build ]]; then
  printf '#include <stdio.h>\nint main(void){puts("c-ok");return 0;}\n' > /tmp/smoke.c
  gcc /tmp/smoke.c -o /tmp/smoke-c
  /tmp/smoke-c | grep c-ok
  printf '#include <iostream>\nint main(){std::cout<<"cpp-ok";}\n' > /tmp/smoke.cpp
  g++ /tmp/smoke.cpp -o /tmp/smoke-cpp
  /tmp/smoke-cpp | grep cpp-ok
  python3-config --includes
  cmake --version
  ninja --version
  git --version
  make --version
  # Exercise Python C extension compilation through the actual headers.
  gcc -shared -fPIC $(python3-config --includes) /tests/native.c -o /tmp/native_smoke.so
  PYTHONPATH=/tmp python -c 'import native_smoke; assert native_smoke.answer() == 42'
  gcc -shared -fPIC -I/usr/local/include/node /tests/node_native.c -o /tmp/node_native.node
  node -e 'require("node:assert").equal(require("/tmp/node_native.node").answer(),42)'
fi
echo "PASS functional $variant $(uname -m)"
